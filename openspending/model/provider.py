from cubes.providers import ModelProvider
from cubes.model import Cube, Measure, MeasureAggregate, create_dimension
from cubes.backends.sql.store import SQLStore, OPTION_TYPES
from cubes.errors import NoSuchCubeError, NoSuchDimensionError
from cubes.common import coalesce_options
from cubes.logging import get_logger

from openspending.core import db
from openspending.model import Dataset


class OpenSpendingModelProvider(ModelProvider):
    __extension_name__ = 'openspending'

    def __init__(self, *args, **kwargs):
        super(OpenSpendingModelProvider, self).__init__(*args, **kwargs)

    def requires_store(self):
        return True

    def cube(self, name, locale=None):
        dataset = Dataset.by_name(name)
        if name is None:
            raise NoSuchCubeError("Unknown dataset %s" % name, name)

        mappings = {}
        joins = []
        fact_table = dataset.model.table.name

        aggregates = [MeasureAggregate('num_entries',
                                       label='Numer of entries',
                                       function='count')]
        measures = []
        for measure in dataset.model.measures:
            cubes_measure = Measure(measure.name, label=measure.label)
            measures.append(cubes_measure)
            aggregate = MeasureAggregate(measure.name,
                                         label=measure.label,
                                         measure=measure.name,
                                         function='sum')
            aggregates.append(aggregate)

        dimensions = []
        for dim in dataset.model.dimensions:
            meta = dim.to_cubes(mappings, joins)
            meta.update({'name': dim.name, 'label': dim.label})
            dimensions.append(create_dimension(meta))

        return Cube(name=dataset.name,
                    fact=fact_table,
                    aggregates=aggregates,
                    measures=measures,
                    label=dataset.label,
                    description=dataset.description,
                    dimensions=dimensions,
                    store=self.store,
                    mappings=mappings,
                    joins=joins)

    def dimension(self, name, locale=None, templates=[]):
        raise NoSuchDimensionError('No global dimensions in OS', name)

    def list_cubes(self):
        cubes = []
        for dataset in Dataset.all_by_account(None):
            if not len(dataset.mapping):
                continue
            cubes.append({
                'name': dataset.name,
                'label': dataset.label
            })
        return cubes


class OpenSpendingStore(SQLStore):
    related_model_provider = "openspending"

    def model_provider_name(self):
        return self.related_model_provider

    def __init__(self, **options):
        super(SQLStore, self).__init__(**options)
        options = dict(options)
        self.options = coalesce_options(options, OPTION_TYPES)
        self.logger = get_logger()
        self.schema = None
        self._metadata = None

    @property
    def connectable(self):
        return db.engine
        
    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = db.MetaData(bind=self.connectable)
        return self._metadata
