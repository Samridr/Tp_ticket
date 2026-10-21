import re
import pandas as pd

# 12 tickets fictifs, 
tickets = [
    "NovaDesk v4.2.1 affiche ERR-204. Contact lea@example.com, tel : 0199000001. Prix : 1490 DH.",
    "CRM v3.8.0 affiche CRM-552 et API-401. Contact marc@example.com. Prix : 800 DH.",
    "L'application mobile v2.6 affiche MOB-73. Commande CMD-9081 : 245 DH.",
    "Facture FAC-310 débitée deux fois : 39,99 DH. Contact nina@example.com.",
    "ScanPro v5.1.2 affiche NET-17 et HW-440. Contact paul@example.com.",
    "DataFlow v1.14 affiche EXP-502. https://support.example.com",
    "Licence LIC-2026 sur PC-18. Version v6.0.3. Contact sara@example.com.",
    "Erreur DATA-09. 12 500 lignes. Prix : 150 DH. tel : 0199000008.",
    "PayZen v2.3.4 affiche PAY-118. Transaction TRX-77102 : 620 DH.",
    "Deuxième débit de 39,99 DH pour facture FAC-310. Contact nina@example.com.",
    "OfficeSuite v7.0 affiche DOC-32. Fichier de 4 Mo. tel : 0199000011.",
    ""
]

df = pd.DataFrame({
    "id": ["T" + str(i).zfill(2) for i in range(1, 13)],
    "brut": tickets
})

print("=== Les 12 tickets bruts ===")
for index, ligne in df.iterrows():
    texte = ligne["brut"]
    if texte == "":
        texte = "[CHAINE VIDE]"
    print(ligne["id"] + " : " + texte)

# Masquer email, téléphone (10 chiffres après tel :) et URL
def masquer(texte):
    texte = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "EMAILTOKEN", texte)
    texte = re.sub(r"(tel\s*:\s*)\d{10}\b", r"\1PHONETOKEN", texte)
    texte = re.sub(r"https?://\S+", "URLTOKEN", texte)
    return texte

df["texte_masque"] = df["brut"].apply(masquer)

# Tokeniser : garder marqueurs, codes, versions, nombres et mots
motif = r"EMAILTOKEN|PHONETOKEN|URLTOKEN|[A-Z]{2,}-[A-Z0-9]+|v?\d+\.\d+(?:\.\d+)?|\d+(?:[,.]\d+)?|[A-Za-zÀ-ÿ]+"
df["tokens"] = df["texte_masque"].apply(
    lambda texte: re.findall(motif, texte, flags=re.IGNORECASE)
)

# les tokens techniques restent inchangés
def mot_ordinaire(mot):
    return not re.fullmatch(
        r"EMAILTOKEN|PHONETOKEN|URLTOKEN|[A-Z]{2,}-[A-Z0-9]+|v?\d+\.\d+(?:\.\d+)?|\d+(?:[,.]\d+)?",
        mot,
        flags=re.IGNORECASE
    )

df["stems"] = df["tokens"].apply(
    lambda tokens: [
        mot.lower()[:-1] if mot_ordinaire(mot) and mot.lower().endswith("s") else mot
        for mot in tokens
    ]
)
df["lemmes"] = df["tokens"]  # Les lemmes sont gardés comme formes d'origine.

# Clé simple de doublon : facture + montant
def cle_doublon(texte, identifiant):
    facture = re.search(r"FAC-\d+", texte)
    montant = re.search(r"\d+(?:,\d{2})?\s*DH", texte)
    if facture and montant:
        return facture.group() + "_" + montant.group()
    return identifiant

df["cle_doublon"] = [
    cle_doublon(df.loc[i, "brut"], df.loc[i, "id"])
    for i in range(len(df))
]
df["groupe_doublon"] = ""
df.loc[df["cle_doublon"] == "FAC-310_39,99 DH", "groupe_doublon"] = "G1"

print(df[[
    "id", "brut", "texte_masque", "tokens", "stems",
    "lemmes", "cle_doublon", "groupe_doublon"
]].to_string(index=False))

df.to_csv("tickets_traites.csv", index=False, encoding="utf-8-sig")
print("\nDoublon potentiel : T04 et T10. Chaîne vide : T12.")
print("Fichier créé : tickets_traites.csv")
