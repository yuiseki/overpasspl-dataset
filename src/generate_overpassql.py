import time
import hashlib
import os
import sys
import ollama
from langchain_chroma import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_community.embeddings import OllamaEmbeddings

base_path = sys.argv[1]
print("base_path:", base_path)

# if already saved, skip validation and save
save_path = os.path.join(base_path, "output-001.overpassql")
print("save_path:", save_path)
if os.path.exists(save_path):
    print("OverpassQL already saved!")
    sys.exit(0)


instruct_file_path = os.path.join(base_path, "input-trident.txt")
instruct = open(instruct_file_path, "r").read().strip()
print("instruct:", instruct)

filter_type = instruct.split(":")[0].strip()
print("filter_type:", filter_type)

embeddings = OllamaEmbeddings(
    model="all-minilm:l6-v2",
    # model="nomic-embed-text:v1.5",
    # model="mxbai-embed-large:v1",
)
vectorstore = Chroma("langchain_store", embeddings)

example_selector = SemanticSimilarityExampleSelector(
    vectorstore=vectorstore,
    k=6,
)


def add_examples_from_dir(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == "input-trident.txt":
                input_txt = open(os.path.join(root, file), "r").read().strip()
                if not input_txt.startswith(filter_type):
                    continue
                # search all output-*.overpassql files
                output_files = [
                    f for f in files if f.startswith("output-") and f.endswith(".overpassql")
                ]
                for output_file in output_files:
                    output_txt = open(os.path.join(
                        root, output_file), "r").read().strip()
                    example = {
                        "input": input_txt,
                        "output": output_txt,
                    }
                    example_selector.add_example(example)


dir_path = "./data"
add_examples_from_dir(dir_path)


prompt_prefix = """\
You are an expert of OpenStreetMap and Overpass API. You output the best Overpass API query based on input text.

You will always reply according to the following rules:
- Output valid Overpass API query.
- The query timeout MUST be 30000.
- The query will utilize a area specifier as needed.
- The query will search nwr as needed.
- The query MUST be out geom.
- The query MUST be enclosed by three backticks on new lines, denoting that it is a code block.
- Respect examples with the utmost precision.
- Take utmost care with the Important note.

===
Examples:\
"""


example_prompt = PromptTemplate(
    input_variables=["input", "output"],
    template="Input:\n{input}\n\nOutput:\n```\n{output}\n```",
)

prompt_template = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=example_prompt,
    prefix=prompt_prefix,
    suffix="Input:\n{question}\n\nOutput:",
    input_variables=["question"],
)

question = f"{instruct}"
prompt = prompt_template.format(question=question)

response = ollama.generate(
    prompt=prompt,
    model='tinydolphin:1.1b',
    # model='tinyllama:1.1b',
    # model='phi3:3.8b',
    options={
        'temperature': 0.01,
        'num_predict': 256,
    })

# extract the OverpassQL from the response
overpassql = response['response'].split("```")[1].strip()

print("Generated OverpassQL:")
print("===")
print(overpassql)
print("===")

# overpassql must be greater than 0 lines and less than 20 lines
if len(overpassql.split("\n")) == 0 or len(overpassql.split("\n")) > 20:
    print("OverpassQL is not valid!")
    sys.exit(1)


def get_number_of_elements(query):
    import httpx

    params = {
        'data': query
    }
    overpass_api_endpoint = "https://z.overpass-api.de/api/interpreter"
    try:
        response = httpx.get(overpass_api_endpoint,
                             params=params, timeout=None)
        response_json = response.json()

        number_of_elements = len(response_json['elements'])
        return number_of_elements
    except Exception as e:
        print("Error:", e)
        return 0


number_of_elements = get_number_of_elements(overpassql)

print("number of elements:", number_of_elements)


if 0 < number_of_elements:
    # mkdir ./tmp/{query_hash}/
    os.makedirs(base_path, exist_ok=True)
    # output the OverpassQL to a file to ./tmp
    with open(save_path, 'w') as f:
        f.write(overpassql+"\n")

print(save_path)

time.sleep(10)

print("")
print("")
