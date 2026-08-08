from dotenv import load_dotenv
import os, time
from openai import OpenAI, RateLimitError, APIError, AsyncOpenAI
import redis



load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
aclient = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "text-embedding-3-small"
BATCH = 100

def embed_batch(texts):
    '''Embed a list of strings
    Return vectors in same order as input'''
    for attempt in range(5):
        try:
            resp = client.embeddings.create(model=MODEL, input=texts)
            break
        except RateLimitError:
            wait = 2 ** attempt
            print(f" rate limited, sleeping {wait}s")
            time.sleep(wait)
        except APIError as e:
            if attempt == 4:
                raise
            print(f" api error ({e}), retry {attempt + 1}/5")
            time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"embedding batch failed after 5 attempts")

    '''Sort by index'''
    vectors = [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]

    assert len(vectors) == len(texts), f"{len(vectors)} vectors vs {len(texts)} rows"
    return vectors

async def embed_query(text):
    '''Single string - used for user's query'''
    resp = await aclient.embeddings.create(model=MODEL, input=text)
    return resp.data[0].embedding




