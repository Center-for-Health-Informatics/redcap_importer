




# this should eventually return a pandas dataframe, right now is array of arrays
def render_instrument_queryset_as_table(qInstrument):
    if not qInstrument:
        return None
    
    # set headers
    headers = []
    oInstrument = qInstrument[0]
    for field in oInstrument._meta.get_fields():
        headers.append(field.name)
        
    if qInstrument[0]._meta.get_fields()[0].name == 'visit_form_viseqver_lookup':
        print('essss')
        for oInstrument in qInstrument:
            print(oInstrument.visdat)

    
    # set data
    data = []    
    for oInstrument in qInstrument:
        record = []
        for field in oInstrument._meta.get_fields():
            try:
                record.append(getattr(oInstrument, field.name))
            except:
                record.append('[M2M Field]')
                # print(oInstrument, field.name, field.get_internal_type())
        data.append(record)
        
    return {'headers' : headers, 'data' : data}