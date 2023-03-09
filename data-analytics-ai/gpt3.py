import openai

def gpt_promt(message):
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "system", "content": "You are an actuary."},
            {"role": "user", "content": message},
        ])
    return response.choices[0]['message']

def gpt_promt_davinci(message):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=message,
        temperature=0.2,
        max_tokens=1000)
    return response.choices[0]['text']