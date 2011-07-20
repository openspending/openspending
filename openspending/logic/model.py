from datetime import datetime

from openspending.model import Model, Account, default_mapping


def save_model(account, **kwargs):
    model = Model(
            author=account.name,
            time=datetime.now(),
            **kwargs)
    return Model.c.insert(model)


def _model_name(model):
    author = model.get('author')
    account = Account.by_name(author)
    if account is not None:
        author = account.get('fullname', author)
    return "%s at %s; based on: %s" % (
            author,
            model.get('time').strftime('%Y.%m.%d - %H:%M'),
            model.get('dataset').get('source_description',
               model.get('dataset').get('name'))
            )


def available_models(package_name):
    models = [{"time": datetime(2000, 1, 1),
               "name": "Default Model",
               "model": {'mapping': default_mapping}}]
    for model in Model.find({"dataset.name": package_name}):
        models.append({
            "time": model.get('time'),
            "name": _model_name(model),
            "model": model
            })
    return sorted(models, key=lambda m: m.get('time'))


