import time
import re

def make_batch_job_body(project_name, input_paths, output_path,
        model_name, region, data_format='JSON',
        version_name=None, max_worker_count=None,
        runtime_version=None):

    project_id = 'projects/{}'.format(project_name)
    model_id = '{}/models/{}'.format(project_id, model_name)
    if version_name:
        version_id = '{}/versions/{}'.format(model_id, version_name)

    # Make a jobName of the format "model_name_batch_predict_YYYYMMDD_HHMMSS"
    timestamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime())

    # Make sure the project name is formatted correctly to work as the basis
    # of a valid job name.
    clean_project_name = re.sub(r'\W+', '_', project_name)

    job_id = '{}_{}_{}'.format(clean_project_name, model_name,
                           timestamp)

    # Start building the request dictionary with required information.
    body = {'jobId': job_id,
            'predictionInput': {
                'dataFormat': data_format,
                'inputPaths': input_paths,
                'outputPath': output_path,
                'region': region}}

    # Use the version if present, the model (its default version) if not.
    if version_name:
        body['predictionInput']['versionName'] = version_id
    else:
        body['predictionInput']['modelName'] = model_id

    # Only include a maximum number of workers or a runtime version if specified.
    # Otherwise let the service use its defaults.
    if max_worker_count:
        body['predictionInput']['maxWorkerCount'] = max_worker_count

    if runtime_version:
        body['predictionInput']['runtimeVersion'] = runtime_version

    return body