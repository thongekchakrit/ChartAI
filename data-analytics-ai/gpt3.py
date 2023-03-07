import openai

def gpt_promt(message):
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "system", "content": "You are an actuary."},
            {"role": "user", "content": message},
        ])
    return response.choices[0]['message']