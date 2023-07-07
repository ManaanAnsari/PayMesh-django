import json


def getABI(contract_name):
    if contract_name == "ERC20":
        f = open("backend/abi/ERC20.json")
        return json.load(f)
    return None
