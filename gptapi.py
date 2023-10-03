import openai


def reformulate_text(text):
    openai.api_key = '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'

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"reformuler sans modifier le sens exacte du texte en donnant des informations précises sur le contenu du texte suivant: '{text}'",
        max_tokens=400
    )

    return response


def details_reponse(text):
    openai.api_key = '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'

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Veuillez donner une information trés précise sans modifier le sens exacte du texte suivant: .'{text}'",
        max_tokens=400
    )

    return response


def formuledepolitesse(text):
    openai.api_key = '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'

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Répondre à la formule de politesse suivante : '{text}'",
        max_tokens=350
    )

    return response

def creation_template():
    openai.api_key = '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'
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Donnez-moi un template de déploiement dans un fichier .yml d'un MySQL sur kubernetes.",
        max_tokens=400
    )

    return response

res = creation_template()
print(res.choices[0].text.strip())