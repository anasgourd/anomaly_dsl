
from textx import metamodel_from_file

from textx.export import metamodel_export,model_export
# Load grammar
meta = metamodel_from_file('anomaly.tx')
metamodel_export(meta, 'anomaly.dot')
# Parse model
model = meta.model_from_file('example.anomaly')

print("DSL is valid")

model_export(model, 'example_model.dot')
