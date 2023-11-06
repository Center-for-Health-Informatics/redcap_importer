from setuptools import setup, find_packages

setup(
    name="redcap_importer",
    version="1.2.0",
    description="Redcap Importer tool source",
    url="https://github.com/Center-for-Health-Informatics/redcap_importer",
    author="John Meinken",
    author_email="meinkejf@ucmail.uc.edu",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Django >= 2.0",
        "django-crispy-forms",
        "requests",
        "python-dateutil",
        "dateparser",
    ],
)
