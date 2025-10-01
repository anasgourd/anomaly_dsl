
import os
import jinja2
from textx import metamodel_from_file

from pprint import pprint

# Load metamodel and model
mm = metamodel_from_file('anomaly.tx', auto_init_attributes=True)
model = mm.model_from_file('example.anomaly')

preprocessing_map = {p.name: p for p in model.preprocesses}

# Assuming one AnomalySpec; loop over all if multiple
spec = model.spec  # Use model.spec if there are multiple

preprocessing_map = {p.name: p for p in model.preprocesses}
# Extract scaler details safely
preprocessor_name = spec.preprocessor.name if spec.preprocessor else None
preprocessor_method = preprocessing_map[preprocessor_name].method if preprocessor_name in preprocessing_map else None

# Map profiles by name
profile_map = {p.name: p for p in model.profiles}

# Extract profile
profile = profile_map[spec.profile.name] if spec.profile and spec.profile.name in profile_map else None
# Extract broker details
# Map brokers by name
broker_map = {b.name: b for b in model.brokers}
broker = broker_map[spec.broker.name] if spec.broker and spec.broker.name in broker_map else None

redis_map = {r.name: r for r in model.redis_dbs}
redis = redis_map[spec.redis.name] if spec.redis and spec.redis.name in redis_map else None

if model.evaluation:
    eval_block = model.evaluation
    evaluation = {
            "name": eval_block.name,
             "data_file": eval_block.data_file,
             "scores_file": eval_block.scores_file,
             "labels_file": eval_block.labels_file,
             "anomalies_file": eval_block.anomalies_file,
             "metrics": [m for m in eval_block.metrics]
    }
else:
    evaluation = None



def parse_output(output_block):
    block_type = output_block.__class__.__name__

    if block_type in ("OutputFile", "AlertFile"):
        return {
            "type": "file",
            "path": output_block.path
        }

    elif block_type in ("OutputMQTT", "AlertMQTT"):
        topic_block = output_block.topicBlock
        broker = topic_block.broker
        auth = getattr(broker, "auth", None)
        auth_type = type(auth).__name__ if auth else None
        auth_data = {}

        if auth_type == "AuthPlain":
            auth_data = {
                "username": auth.username,
                "password": auth.password
            }
        elif auth_type == "AuthApiKey":
            auth_data = {
                "key": auth.key
            }
        elif auth_type == "AuthCert":
            auth_data = {
                "cert": getattr(auth, "cert", None),
                "certPath": getattr(auth, "certPath", None)
            }
        return {
            "type": "mqtt",
            "topic": topic_block.topic,
            "broker": {
                "host": topic_block.broker.host,
                "port": topic_block.broker.port,
                "ssl": getattr(broker, "ssl", False),
                "webPath": getattr(broker, "webPath", ""),
                "webPort": getattr(broker, "webPort", 0),
                "auth": auth_data
	   }
        }

    return None


# Extract auth if present
auth = getattr(broker, "auth", None) if broker else None

# Determine auth fields based on type
auth_type = type(auth).__name__ if auth else None
auth_data = {}
if auth_type == "AuthPlain":
    auth_data = {
        "username": auth.username,
        "password": auth.password
    }
elif auth_type == "AuthApiKey":
    auth_data = {
        "key": auth.key
    }
elif auth_type == "AuthCert":
    auth_data = {
        "cert": getattr(auth, "cert", None),
        "certPath": getattr(auth, "certPath", None)
    }
context = {
    "spec": {
        "attribute": spec.attribute,
        "topic":spec.topic,
        "profile": {
            "threshold": profile.threshold if profile else None,
            "start_index": profile.start_index if profile else None
        },
        "output": parse_output(spec.output),
        "alerts": parse_output(spec.alerts),
        "preprocessor_name": preprocessor_name,
        "preprocessor_method": preprocessor_method,
        "model": spec.model,
        "model_name": type(spec.model).__name__,
        "broker": {
            "host": broker.host if broker else None,
            "port": broker.port if broker else None,
            "ssl": getattr(broker, "ssl", None),
            "basePath": getattr(broker, "basePath", None),
            "webPath": getattr(broker, "webPath", None),
            "webPort": getattr(broker, "webPort", None),
            "auth_type": auth_type,
            "auth": auth_data
        },
        "redis": {
            "host": redis.host if redis else None,
            "port": redis.port if redis else None,
            "db": redis.db if redis else None,
            "key_scores": getattr(redis, "key_scores", "anomaly_scores") if redis else None,
             "key_alerts": getattr(redis, "key_alerts", "anomaly_alerts") if redis else None
    }

    },
    "evaluation": evaluation
}

template_loader = jinja2.FileSystemLoader(searchpath=".")
template_env = jinja2.Environment(loader=template_loader)
template = template_env.get_template("pipeline_template.j2")

# Render and write to file
output_code = template.render(context)
with open("anomaly_pipeline.py", "w") as f:
        f.write(output_code)

        print("Generated 'anomaly_pipeline.py' from DSL and template.") 


