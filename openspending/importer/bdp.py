from openspending.model import meta as db
from openspending.model.dataset import Dataset
from openspending.model.source import Source
from budgetdatapackage import BudgetDataPackage

import urlparse
import logging
log = logging.getLogger(__name__)


class BudgetDataPackageMap(object):
    """
    Budget Data Package Mapper/Modeller. This class contains properties which
    all consist of the OpenSpending model equivalent for the budget data
    package properties.
    """

    def __init__(self, schema):
        # We lowercase the field names just in case
        self.fields = [f['name'] for f in schema['fields']]

    def id_label_map(self, name, label):
        """
        Create a compound dimension with and id (name) and a label.
        By default this uses the label as the name but if the id is
        found in fields it replaces the label for the name and also
        if the label is not found it uses the name instead.

        If neither name nor label is in the fields this returns None.
        """

        # We need either name or label to continue
        if name not in self.fields and label not in self.fields:
            return None

        # Model description with label for everything
        description = {
            "attributes": {
                "label": {
                    "datatype": "string",
                    "column": label,
                    "default_value": ""
                },
                "name": {
                    "datatype": "id",
                    "column": label,
                    "default_value": ""
                }
            },
            "type": "compound",
        }

        # Replace label with name if that exists in the fields
        if name in self.fields:
            description['attributes']['name']['column'] = name
        # Replace label with name if label doesn't exist in the fields
        if label not in self.fields:
            description['attributes']['label']['column'] = name

        return description

    @property
    def amount(self):
        return {
            'amount': {
                "default_value": "",
                "description": "Amount",
                "column": "amount",
                "label": "Amount",
                "datatype": "float",
                "type": "measure"
            }
        }

    @property
    def row_id(self):
        """
        This is a replacement for the budget data package id row which
        unfortunately cannot be used in OpenSpending models.
        """
        return {
            'row_id': {
                "default_value": "",
                "description": "Unique row id",
                "column": "row_id",
                "label": "Row id",
                "datatype": "string",
                "key": True,
                "type": "attribute"
            }
        }

    @property
    def code(self):
        if 'code' in self.fields:
            return {
                "code": {
                    "default_value": "",
                    "description": "Internal code",
                    "column": "code",
                    "label": "Code",
                    "datatype": "string",
                    "type": "attribute"
                }
            }
        return None

    @property
    def description(self):
        if 'description' in self.fields:
            return {
                "description": {
                    "default_value": "",
                    "description": "Description",
                    "column": "description",
                    "label": "Description",
                    "datatype": "string",
                    "type": "attribute"
                },
            }

        return None

    @property
    def admin(self):
        if 'admin' not in self.fields:
            return None
        attributes = {
            "label": {
                "datatype": "string",
                "column": "admin",
                "default_value": ""
            },
            "name": {
                "datatype": "id",
                "column": "admin",
                "default_value": ""
            }
        }

        if 'adminID' in self.fields:
            attributes['name']['column'] = 'adminID'

        if 'adminOrgID' in self.fields:
            attributes['adminOrgID'] = {
                "datatype": "string",
                "column": "adminOrgID",
                "default_value": ""
            }

        return {
            "from": {
                "attributes": attributes,
                "facet": True,
                "type": "compound",
                "description": "Administrative entity responsible",
                "label": "Admin"
            }
        }

    @property
    def cofog(self):
        """
        Creates three COFOG fields, one for each of the three levels of COFOG.
        Budget data packages use a single field to represent COFOG but for it
        to be useful in OpenSpending we need to map them into three separate
        fields.
        """
        if 'cofog' not in self.fields:
            return None

        cofog_map = {}
        for level in range(1, 4):
            cofog_map['cofog{level}'.format(level=level)] = {
                "label": "Cofog {level}".format(level=level),
                "description": "COFOG - Level {level}".format(level=level),
                "attributes": {
                    "name": {
                        "column": "cofog{level}code".format(level=level),
                        "datatype": "id",
                        "default_value": ""
                    },
                    "label": {
                        "column": "cofog{level}label".format(level=level),
                        "datatype": "string",
                        "default_value": ""
                    }
                },
                "type": "compound"
            }

        # Cofog 1 should be a facet
        cofog_map['cofog1']['facet'] = True
        return cofog_map

    @property
    def economic(self):
        field_map = self.id_label_map('economicID', 'economic')
        if field_map is None:
            return None
        field_map["description"] = "Economic classification"
        field_map["label"] = "Economic"
        return {"economic": field_map}

    @property
    def source(self):
        if 'financialsource' in self.fields:
            return {
                "financialsource": {
                    "default_value": "",
                    "description": "Financial source",
                    "column": "financialSource",
                    "label": "Financial Source",
                    "datatype": "string",
                    "type": "attribute"
                }
            }

        return None

    @property
    def functional(self):
        field_map = self.id_label_map('funcationalID', 'funcational')
        if field_map is None:
            return None
        field_map["description"] = "Functional classification"
        field_map["label"] = "Funcational"
        return {"functional": field_map}

    @property
    def fund(self):
        field_map = self.id_label_map('fundID', 'fund')
        if field_map is None:
            return None
        field_map["description"] = "Fund"
        field_map["label"] = "Source fund"
        return {"fund": field_map}

    @property
    def geocode(self):
        if 'geocode' in self.fields:
            return {
                "geocode": {
                    "default_value": "",
                    "description": "Geographical area",
                    "column": "geocode",
                    "label": "Geocode",
                    "datatype": "string",
                    "type": "attribute"
                }
            }

        return None

    @property
    def gfsmexpense(self):
        """
        Same as with COFOG, this creates three separate fields out of a single
        field in the Budget Data Package
        """

        if 'gfsmexpense' not in self.fields:
            return None

        gfsm_map = {}
        for level in range(1, 4):
            gfsm_map["gfsmexpense{level}".format(level)] = {
                "default_value": "",
                "description": "GFSM 2001 - Level {level}".format(level=level),
                "column": "gfsmexpense{level}".format(level=level),
                "label": "GFSM Expense {level}".format(level=level),
                "datatype": "string",
                "type": "attribute"
            }

        return gfsm_map

    @property
    def program(self):
        field_map = self.id_label_map('programID', 'program')
        if field_map is None:
            return None
        field_map["description"] = "Program"
        field_map["label"] = "Program"
        return {"program": field_map}

    @property
    def project(self):
        field_map = self.id_label_map('projectID', 'project')
        if field_map is None:
            return None
        field_map["description"] = "Project"
        field_map["label"] = "Project"
        return {"project": field_map}

    @property
    def purchaser(self):
        field_map = self.id_label_map('purchaserID', 'purchaserOrgID')
        if field_map is None:
            return None
        field_map["description"] = "Purchaser"
        field_map["label"] = "Purchaser"
        return {"purchaser": field_map}

    @property
    def type(self):
        if 'type' in self.fields:
            return {
                "type": {
                    "default_value": "",
                    "description": "Budgetary classification",
                    "column": "type",
                    "label": "BudgetaryClassification",
                    "datatype": "string",
                    "type": "attribute"
                }
            }

        return None

    @property
    def gfsmrevenue(self):
        """
        Same as with COFOG this creates three separate fields out of a single
        field in a Budget Data Package
        """

        if 'gfsmrevenue' not in self.fields:
            return None
        revenue_map = {}
        for level in range(1, 4):
            revenue_map['gfsmrevenue{level}'.format(level=level)] = {
                "default_value": "",
                "description": "GFSM 2001 revenue, level {level}".format(
                    level=level),
                "column": "gfsmrevenue{level}".format(level=level),
                "label": "GFSMrevenue{level}".format(level=level),
                "datatype": "string",
                "type": "attribute"
            }

        return revenue_map

    @property
    def supplier(self):
        if 'supplier' in self.fields:
            return {
                "supplier": {
                    "default_value": "",
                    "description": "Supplier",
                    "column": "supplier",
                    "label": "Supplier",
                    "datatype": "string",
                    "type": "attribute"
                }
            }

        return None

    @property
    def time(self):
        return {
            "time": {
                "default_value": "",
                "description": "Date",
                "column": "time",
                "label": "Date",
                "datatype": "date",
                "type": "date"
            }
        }

    @property
    def amountadjusted(self):
        if 'amountadjusted' in self.fields:
            return {
                "amountadjusted": {
                    "default_value": "",
                    "description": "Amount (Adjusted)",
                    "column": "amountadjusted",
                    "label": "Amount Adjusted",
                    "datatype": "float",
                    "type": "measure"
                }
            }

        return None

    @property
    def amountbudgeted(self):
        if 'amountbudgeted' in self.fields:
            return {
                "amountbudgeted": {
                    "default_value": "",
                    "description": "Amount (Budgeted)",
                    "column": "amountbudgeted",
                    "label": "Amount Budgeted",
                    "datatype": "float",
                    "type": "measure"
                }
            }

        return None

    @property
    def budgetlineitem(self):
        if 'budgetlineitem' in self.fields:
            return {
                "budgetlineitem": {
                    "default_value": "",
                    "description": "Budget line item",
                    "column": "budgetlineitem",
                    "label": "Budget Line Item",
                    "datatype": "string",
                    "type": "attribute"
                }
            }

        return None

    @property
    def contract(self):
        if 'contractID' in self.fields:
            return {
                "contractid": {
                    "default_value": "",
                    "description": "Contract id",
                    "column": "contractID",
                    "label": "Contract ID",
                    "datatype": "string",
                    "type": "attribute"
                }
            }

        return None

    @property
    def dateadjusted(self):
        if 'dateadjusted' in self.fields:
            return {
                "dateadjusted": {
                    "default_value": "",
                    "description": "Date (Adjusted)",
                    "column": "dateadjusted",
                    "label": "Date Adjusted",
                    "datatype": "date",
                    "type": "date"
                }
            }

        return None

    @property
    def datebudgeted(self):
        if 'datebudgeted' in self.fields:
            return {
                "datebudgeted": {
                    "default_value": "",
                    "description": "Date (Budgeted)",
                    "column": "datebudgeted",
                    "label": "Date Budgeted",
                    "datatype": "date",
                    "type": "date"
                }
            }

        return None

    @property
    def datereported(self):
        if 'datereported' in self.fields:
            return {
                "datereported": {
                    "default_value": "",
                    "description": "Date (Reported)",
                    "column": "datereported",
                    "label": "Date Reported",
                    "datatype": "date",
                    "type": "date"
                }
            }

        return None

    @property
    def invoice(self):
        if 'invoiceID' in self.fields:
            return {
                "invoiceid": {
                    "default_value": "",
                    "description": "Invoice id",
                    "column": "invoiceID",
                    "label": "Invoiceid",
                    "datatype": "string",
                    "type": "attribute"
                }
            }

        return None


def create_budget_data_package(url, user, private):
    try:
        bdpkg = BudgetDataPackage(url)
    except Exception as problem:
        # Lots of different types of problems can arise with a
        # BudgetDataPackage, but their message should be understandable
        # so we catch just any Exception and email it's message to the user
        log.error("Failed to parse budget data package: {0}".format(
            problem.message))
        return []

    sources = []
    for (idx, resource) in enumerate(bdpkg.resources):
        dataset = Dataset.by_name(bdpkg.name)
        if dataset is None:
            # Get information from the descriptior file for the given
            # resource (at index idx)
            info = get_dataset_info_from_descriptor(bdpkg, idx)
            # Set the dataset name based on the previously computed one
            info['dataset']['name'] = bdpkg.name
            # Create the model from the resource schema
            model = create_model_from_schema(resource.schema)
            # Set the default value for the time to the fiscal year of the
            # resource, because it isn't included in the budget CSV so we
            # won't be able to load it along with the data.
            model['time']['default_value'] = resource.fiscalYear
            # Add the model as the mapping
            info['mapping'] = model

            # Create the dataset
            dataset = Dataset(info)
            dataset.managers.append(user)
            dataset.private = private
            db.session.add(dataset)
            db.session.commit()
        else:
            if not dataset.can_update(user):
                log.error(
                    "User {0} not permitted to update dataset {1}".format(
                        user.name, bdpkg.name))
                return []

        if 'url' in resource:
            resource_url = resource.url
        elif 'path' in resource:
            if 'base' in bdpkg:
                resource_url = urlparse.urljoin(bdpkg.base, resource.path)
            else:
                resource_url = urlparse.urljoin(url, resource.path)
        else:
            log.error('Url not found')
            return []

        # We do not re-add old sources so if we find the same source
        # we don't do anything, else we create the source and append it
        # to the source list
        for dataset_source in dataset.sources:
            if dataset_source.url == resource_url:
                break
        else:
            source = Source(dataset=dataset, creator=user,
                            url=resource_url)
            db.session.add(source)
            db.session.commit()
            sources.append(source)

    return sources


def create_model_from_schema(schema):
    """Create a model for the dataset based on the schema defined in the
    descriptor file"""
    bdp_map = BudgetDataPackageMap(schema)
    model = {}
    # Loop over all supported fields
    # Currently this goes over all fields, but it would be better to restrict
    # the fiels to the type of budget data package.
    for field in ['amount', 'row_id', 'code', 'description', 'admin', 'cofog',
                  'economic', 'source', 'functional', 'fund', 'geocode',
                  'gfsmexpense', 'program', 'project', 'purchaser', 'type',
                  'gfsmrevenue', 'supplier', 'time', 'amountadjusted',
                  'amountbudgeted', 'budgetlineitem', 'contract',
                  'dateadjusted', 'datebudgeted', 'datereported', 'invoice']:
        # Check if the map has the field (returns None if it does) and
        # update the model accordingly
        if hasattr(bdp_map, field):
            value = getattr(bdp_map, field)
            if value:
                model.update(value)

    return model


def get_dataset_info_from_descriptor(package, resource):
        pkg_resource = package.resources[resource]
        # This is not entirely correct since aggregated expenditure could
        # be spending, but we still mark it as a budget because we want
        # transactional spending, not aggregated spending
        cat_mapping = {
            'expenditure': {
                'aggregated': 'budget',
                'transactional': 'spending'},
            'revenue': {
                'aggregated': 'other',
                'transactional': 'other'
            }}

        # Get category based on the mapping
        category = cat_mapping[pkg_resource.type][pkg_resource.granularity]
        # Set location/country
        if 'location' in pkg_resource:
            country = [pkg_resource.location]
        else:
            country = []

        return {
            "dataset": {
                "label": package.get("title", pkg_resource.name),
                "description": package.get("description", pkg_resource.name),
                "currency": pkg_resource.currency,
                "category": category,
                "default_time": pkg_resource.fiscalYear,
                "territories": country
            }
        }
