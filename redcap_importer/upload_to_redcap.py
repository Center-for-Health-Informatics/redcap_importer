import json
import datetime
import requests
import dateparser

from redcap_importer.models import RedcapConnection, FieldMetadata, EtlLog


class UploadToRedcap:
    """
    Helps with uploading data to a REDCap project using the API.

    How to use:
    - use init to set redcap project, batch size, etc.
    - use upload() method to upload your data
        - data must be a list of dicts with field:value pairs
        - data must be set up in the structure that the REDCap API expects
    """

    def __init__(
        self,
        redcap_project_name,
        create_log_entry=True,
        batch_size=500,
        user=None,
        initial_comment="",
        file_name=None,
    ):
        self.connection = RedcapConnection.objects.get(unique_name=redcap_project_name)
        self.create_log_entry = create_log_entry
        self.query_count = 0
        self.last_successful_record_number = 0
        self.last_successful_record = ""
        self.batch_size = batch_size
        self.user = user
        self.file_name = file_name
        self.initial_comment = initial_comment

    def start_log_entry(self):
        self.log = EtlLog(
            redcap_project=self.connection.unique_name,
            start_date=datetime.datetime.now(),
            status=EtlLog.STATUS_UPLOAD_STARTED,
            direction=EtlLog.Direction.UPLOAD,
        )
        if self.user:
            self.log.user = self.user.username
        if self.file_name:
            self.log.file_name = self.file_name
        if self.initial_comment:
            self.log.comment = self.initial_comment
        self.log.save()

    def update_log_entry_start_query(self):
        self.log.query_count = self.query_count
        self.log.save()

    def update_log_entry_finish_query(self):
        self.log.last_successful_record_number = self.last_successful_record_number
        self.log.last_successful_record = json.dumps(self.last_successful_record)
        self.log.save()

    def finish_log_entry(self, error_msg=None):
        if error_msg:
            self.log.status = EtlLog.STATUS_UPLOAD_FAILED
            if self.log.comment:
                self.log.comment = self.log.comment + "\n" + error_msg
            else:
                self.log.comment = error_msg
        else:
            self.log.status = EtlLog.STATUS_UPLOAD_COMPLETE
        self.log.query_count = self.query_count
        self.log.end_date = datetime.datetime.now()
        self.log.save()

    def upload(self, dataset):
        """
        dataset should be a list of dicts with field:value pairs
        """
        print("uploading to {}".format(self.connection.unique_name))
        if self.create_log_entry:
            self.start_log_entry()

        try:
            upload_records = []
            for record in dataset:
                next_entry = self.process_record(record)
                upload_records.append(next_entry)
                if len(upload_records) >= self.batch_size:
                    self.upload_batch(upload_records)
                    upload_records = []
            # upload the last group of records
            if upload_records:
                self.upload_batch(upload_records)
        except Exception as e:
            # handle failed load
            print("upload failed")
            if self.create_log_entry:
                self.finish_log_entry(str(e))
            raise e

        # handle successful load
        print("upload complete")
        if self.create_log_entry:
            self.finish_log_entry()

    def upload_batch(self, upload_records):
        upload_json = json.dumps(upload_records)
        response = self.run_request(
            "record",
            {
                "data": upload_json,
                "overwriteBehavior": "overwrite",  # "normal" or "overwrite"
            },
        )
        print(str(response))
        # count will show number of subjects affected, not number of records uploaded
        # if 'count' not in response or response['count'] != len(upload_records):
        #     raise Exception(str(response))
        if "count" not in response or response["count"] == 0:
            raise Exception(str(response))
        else:
            # need to document the last record that uploaded successfully
            self.last_successful_record_number += len(upload_records)
            self.last_successful_record = upload_records[-1]
            self.update_log_entry_finish_query()

    def run_request(self, content, addl_options={}):
        addl_options["content"] = content
        addl_options["token"] = self.connection.get_api_token()
        addl_options["format"] = "json"
        addl_options["returnFormat"] = "json"
        # print(addl_options)
        self.query_count += 1
        if self.create_log_entry:
            self.update_log_entry_start_query()
        return requests.post(self.connection.api_url.url, addl_options).json()
        # print(oConnection.api_url.url, addl_options)
        # return {}

    def process_record(self, record):
        out_record = {}
        for key, val in record.items():
            # try to look up field type
            oField = FieldMetadata.objects.filter(
                instrument__project__connection=self.connection, unique_name=key
            ).first()

            if val is None or val == "":
                out_record[key] = ""
            elif oField and oField.django_data_type == "DateField":
                try:
                    date_val = dateparser.parse(val)
                    out_record[key] = date_val.strftime("%Y-%m-%d")
                except Exception:
                    raise Exception("Unable to parser value {} for date field {}".format(val, key))
            elif isinstance(val, datetime.date):
                out_record[key] = val.strftime("%Y-%m-%d")

            else:
                out_record[key] = val
        return out_record
