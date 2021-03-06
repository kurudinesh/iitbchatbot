from profanityfilter import ProfanityFilter

pf = ProfanityFilter()
def filtertxt(text):
    return pf.censor(text)

print(filtertxt("thats bullshit"))