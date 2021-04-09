import re
import requests
from django.http import JsonResponse
from requests_auth import Basic

from ConcorsoBiblioteca.settings import GESTIONALE_UTENTI_REST_USERNAME, GESTIONALE_UTENTI_REST_PASSWORD, \
    GESTIONALE_UTENTI_ANAGRAFICA_STUDENTI_URL, GESTIONALE_UTENTI_ANAGRAFICA_DIPENDENTI_URL


def studente_filtra_ultimo_valido(dati_list):
    dati_selezionato = dati_list[0]
    for dati_corrente in dati_list:
        if (dati_corrente['aaIscrId'] > dati_selezionato['aaIscrId']) and \
                (dati_corrente['motStaStuCod'] == 'IMM' or dati_corrente['motStaStuCod'] == 'imm'
                 or dati_corrente['motStaStuCod'] == 'IMR' or dati_corrente['motStaStuCod'] == 'imr'):
            dati_selezionato = dati_corrente
    return dati_selezionato

def studente_email(email):
    # Se il formato della email non è corretto solleva eccezione
    if not check_email(email):
        return None
    response = requests.get(GESTIONALE_UTENTI_ANAGRAFICA_STUDENTI_URL[2] + email,
                            auth=Basic(GESTIONALE_UTENTI_REST_USERNAME, GESTIONALE_UTENTI_REST_PASSWORD))

    #Controllo che lo studente esista
    resp = check_list(response.json())
    if resp is not None:
        return_value = studente_filtra_ultimo_valido(response.json())
        return return_value
    else:
        return resp



def dipendente_email(email):
    # Se il formato della email non è corretto solleva eccezione
    if not check_email(email):
        return None

    response = requests.get(GESTIONALE_UTENTI_ANAGRAFICA_DIPENDENTI_URL[2] + email,
                            auth=Basic(GESTIONALE_UTENTI_REST_USERNAME, GESTIONALE_UTENTI_REST_PASSWORD))
    return_value = None
    try:
        return_value = response.json()[0]
    finally:
        return return_value


def check_email(email):
    """Prende in ingresso una stringa
        e controlla che abbia un formato corretto
        come email
            Parameters:
            email: stringa rappresentante l'email da controllare
            :rtype: bool
           """
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'



    if re.search(regex, email):
        return True
    else:
        return False


def check_list(response_json_lista):
    """Prende in ingresso una lista JSON
    e la restituisce come JsonResponse se la lunghezza è != 0
    altrimenti restituisce None
        Parameters:
        response_json_lista (<Lista JSON>): Lista JSON Restituita dall'interrogazione del REST serviceESSE3
        Returns:
        <Lista JSON> o None
       """
    if len(response_json_lista) != 0:
        return JsonResponse(response_json_lista, safe=False)
    else:
        return None



def test_esse3_studente(email):
    if email:
        print('email: ' + email)
        dati = studente_email(email)
        print(dati)


    return studente_email
"""
if __name__ == '__main__':
    test_esse3('l.calabro2@campus.unimib.it', 'CLBLCU78B03B791H', '735656')
    print('\n--------------------------------------------------\n')
    test_esse3('d.musacchioadoris@campus.unimib.it', None, None)
    print('\n--------------------------------------------------\n')
    test_esse3('g.rigaldi@campus.unimib.it', None, None)
    print('\n--------------------------------------------------\n')
"""
