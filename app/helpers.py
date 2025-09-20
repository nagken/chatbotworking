from pygments import highlight, lexers, formatters
import pandas as pd
import json as json_lib
import requests
import json
import altair as alt
import IPython
from IPython.display import display, HTML

def is_json(str):
  try:
      json_object = json_lib.loads(str)
  except ValueError as e:
      return False
  return True

def is_json(str):
    try:
        json_object = json_lib.loads(str)
    except ValueError as e:
        return False
    return True

def handle_text_response(resp):
    parts = resp['parts']
    print(''.join(parts))

def get_property(data, field_name, default = ''):
    return data[field_name] if field_name in data else default

def display_schema(data):
    fields = data['fields']
    df = pd.DataFrame({
        "Column": map(lambda field: get_property(field, 'name'), fields),
        "Type": map(lambda field: get_property(field, 'type'), fields),
        "Description": map(lambda field: get_property(field, 'description', '-'), fields),
        "Mode": map(lambda field: get_property(field, 'mode'), fields)
        })
    display(df)

def display_section_title(text):
    display(HTML('<h2>{}</h2>'.format(text)))

def format_bq_table_ref(table_ref):
    return '{}.{}.{}'.format(table_ref['projectId'], table_ref['datasetId'], table_ref['tableId'])

def format_looker_table_ref(table_ref):
return 'lookmlModel: {}, explore: {}, lookerInstanceUri: {}'.format(table_ref['lookmlModel'], table_ref['explore'], table_ref['lookerInstanceUri'])

def display_datasource(datasource):
    source_name = ''

    if 'studioDatasourceId' in datasource:
        source_name = datasource['studioDatasourceId']
    elif 'lookerExploreReference' in datasource:
        source_name = format_looker_table_ref(datasource['lookerExploreReference'])
    else:
        source_name = format_bq_table_ref(datasource['bigqueryTableReference'])

    print(source_name)
    display_schema(datasource['schema'])

def handle_schema_response(resp):
    if 'query' in resp:
        print(resp['query']['question'])
    elif 'result' in resp:
        display_section_title('Schema resolved')
        print('Data sources:')
        for datasource in resp['result']['datasources']:
            display_datasource(datasource)


def handle_data_response(resp):
    if 'query' in resp:
        query = resp['query']
        display_section_title('Retrieval query')
        print('Query name: {}'.format(query['name']))
        print('Question: {}'.format(query['question']))
        print('Data sources:')
        for datasource in query['datasources']:
            display_datasource(datasource)
    elif 'generatedSql' in resp:
        display_section_title('SQL generated')
        print(resp['generatedSql'])
    elif 'result' in resp:
        display_section_title('Data retrieved')

        fields = map(lambda field: get_property(field, 'name'), resp['result']['schema']['fields'])
        dict = {}

        for field in fields:
            dict[field] = map(lambda el: get_property(el, field), resp['result']['data'])

        display(pd.DataFrame(dict))


def handle_chart_response(resp):
    if 'query' in resp:
        print(resp['query']['instructions'])
    elif 'result' in resp:
        vegaConfig = resp['result']['vegaConfig']
        alt.Chart.from_json(json_lib.dumps(vegaConfig)).display();

def handle_error(resp):
    display_section_title('Error')
    print('Code: {}'.format(resp['code']))
    print('Message: {}'.format(resp['message']))

def get_stream(url, json):
    s = requests.Session()

    acc = ''

    with s.post(url, json=json, headers=headers, stream=True) as resp:
        for line in resp.iter_lines():
            if not line:
                continue

            decoded_line = str(line, encoding='utf-8')

            if decoded_line == '[{':
                acc = '{'
            elif decoded_line == '}]':
                acc += '}'
            elif decoded_line == ',':
                continue
            else:
                acc += decoded_line

            if not is_json(acc):
                continue

            data_json = json_lib.loads(acc)

            if not 'systemMessage' in data_json:
                if 'error' in data_json:
                    handle_error(data_json['error'])
                continue

            if 'text' in data_json['systemMessage']:
                handle_text_response(data_json['systemMessage']['text'])
            elif 'schema' in data_json['systemMessage']:
                handle_schema_response(data_json['systemMessage']['schema'])
            elif 'data' in data_json['systemMessage']:
                handle_data_response(data_json['systemMessage']['data'])
            elif 'chart' in data_json['systemMessage']:
                handle_chart_response(data_json['systemMessage']['chart'])
            else:
                colored_json = highlight(acc, lexers.JsonLexer(), formatters.TerminalFormatter())
                print(colored_json)
                print('\n')
                acc = ''

def get_stream_multi_turn(url, json, conversation_messages):
    s = requests.Session()

    acc = ''

    with s.post(url, json=json, headers=headers, stream=True) as resp:
        for line in resp.iter_lines():
            if not line:
                continue

            decoded_line = str(line, encoding='utf-8')

            if decoded_line == '[{':
                acc = '{'
            elif decoded_line == '}]':
                acc += '}'
            elif decoded_line == ',':
                continue
            else:
                acc += decoded_line

            if not is_json(acc):
                continue

            data_json = json_lib.loads(acc)
            # Store the response that will be used in the next iteration
            conversation_messages.append(data_json)

            if not 'systemMessage' in data_json:
                if 'error' in data_json:
                    handle_error(data_json['error'])
                continue

            if 'text' in data_json['systemMessage']:
                handle_text_response(data_json['systemMessage']['text'])
            elif 'schema' in data_json['systemMessage']:
                handle_schema_response(data_json['systemMessage']['schema'])
            elif 'data' in data_json['systemMessage']:
                handle_data_response(data_json['systemMessage']['data'])
            elif 'chart' in data_json['systemMessage']:
                handle_chart_response(data_json['systemMessage']['chart'])
            else:
                colored_json = highlight(acc, lexers.JsonLexer(), formatters.TerminalFormatter())
                print(colored_json)
            print('\n')
            acc = ''
