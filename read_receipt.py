"""
Author: Alexei Gaidachev
Module: read_receipt, function call: easy_ocr(receipt_img)
Pre-requisites: pip -m install easyocr, Python 3.10+
Info: Super bare-bones interpreting receipt images into text, and JSON, CSV files
Version: 0.0.1
"""
# import sys
import os
import re
# from PIL import Image
from typing import Optional
import easyocr
import csv
# from itertools import zip_longest
# import cv2 as cv
# import numpy as np
# import pytesseract
import pprint
# import unicodedata
import json

# change this absolute path to different receipt directory
PATH_TO_RECEIPTS = os.getcwd() + "/receipts"
PRICE_PATTERN = re.compile(r'([0-9]+\.[0-9]+)')
DEBUGGING = False

# this needs to run only once to load the model into memory
READER = easyocr.Reader(['ch_sim', 'en'])

def main():
    receipt_data = []
    receipt_list = get_receipt_list()
    scanned_receipts = get_files_from_cache(base_name=True)
    print('Scanned Receipts : -------------------------------')
    pprint.pprint(scanned_receipts)
    print()
    for receipt_img in receipt_list:
        if receipt_img in scanned_receipts:
            continue
        print("using receipt: ", receipt_img)
        receipt_img_path = get_receipt_path(receipt_img)
        ocr_data = easy_ocr(receipt_img_path)
        receipt_data.append(ocr_data)
    pprint.pprint(receipt_data)
    if receipt_data:
        write_cache_file(receipt_data)
        write_to_file(receipt_data)


def get_receipt_list() -> list:
    """get receipt images list, assuming we have a clean directory
    :param img_idx: get image index from a list of images
    :return: path-to-image.py
    """
    receipts_list = [l for l in os.listdir(
        PATH_TO_RECEIPTS) if l.endswith('.jpg')]
    if DEBUGGING:
        return [receipts_list[1]]
    return receipts_list


def get_receipt_path(receipt_img) -> str:
    """get the path of the receipt
    :param receipt_img: <str> receipt image
    :return: <str> receipt image path
    """
    return os.path.normpath(os.path.join(PATH_TO_RECEIPTS, receipt_img))


def easy_ocr(receipt_img) -> dict:
    """parse the receipt image
    :param receipt_img: <str> receipt image path
    :return: <dict> receipt data
    """
    receipt_raw = READER.readtext(receipt_img, detail=1, paragraph=False) # list
    length_of_result = len(receipt_raw)
    receipt_data = {}
    print("parsing: {}".format(receipt_img))
    receipt_data["file_name"] = receipt_img
    if DEBUGGING:
        for i in range(length_of_result):
            print(receipt_raw[i][1])
        parse_receipt(length_of_result, receipt_data, receipt_raw)
    else:
        parse_receipt(length_of_result, receipt_data, receipt_raw)
    pprint.pprint(receipt_data)
    return receipt_data

def parse_receipt(length_of_result, receipt_data, receipt_raw):
    """Parses the receipts cleanly
    """
    store_name = parse_store_name(length_of_result, receipt_raw)
    if store_name == 'Costco':
        clean_costco_receipt(length_of_result, receipt_data, receipt_raw)
    else:
        clean_standard_receipt(length_of_result, receipt_data, receipt_raw)

def parse_store_name(length_of_result: int, receipt_raw: list) -> None:
    """loop through the receipts' contents and determine what store it belongs to.
    """
    for i in range(length_of_result):
        if "#" in receipt_raw[i][1]:
            return "Costco"
    return "Standard"

def clean_costco_receipt(length_of_result: int, receipt_data: dict, receipt_raw: list) -> None:
    """standard receipt cleaning from a raw text output of Costco receipt_raw argument
    :param length_of_result: <int> length of the raw result
    :parm receipt_data: <dict> populate this receipt data dict
    :param receipt_raw: <list> supply the raw data list
    """
    for i in range(length_of_result):
        if i == 2:
            # store_location = unicodedata.normalize('NFD', receipt_raw[i][1]).encode('ascii', 'ignore')
            store_location = receipt_raw[i][1]
            receipt_data["store_location"] = "{}".format(str(store_location))
        if i < 5 and "#" in receipt_raw[i][1]:
            receipt_data["store_name"] = "Costco: {}".format(receipt_raw[i][1])
        if i > 1:
            if "groceries" not in receipt_data:
                receipt_data["groceries"] = []
            # match if price has been found
            if PRICE_PATTERN.match(receipt_raw[i][1]):
                name = u"{}".format(receipt_raw[i-1][1])
                # name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')
                price = u"{}".format(PRICE_PATTERN.findall(receipt_raw[i][1])[0])
                if '/k' in receipt_raw[i][1]:
                    continue
                receipt_data["groceries"].append([str(name), price])

def clean_standard_receipt(length_of_result: int, receipt_data: dict, receipt_raw: list) -> None:
    """standard receipt cleaning from a raw text output of standard receipt_raw argument
    Info: No tuples allowed to be written in a JSON file
    :param length_of_result: <int> length of the raw result
    :parm receipt_data: <dict> populate this receipt data dict
    :param receipt_raw: <list> supply the raw data list
    """
    for i in range(length_of_result):
        if i == 0:
            receipt_data["store_name"] = u"{}".format(receipt_raw[i][1])
        if i == 1:
            receipt_data["store_location"] = u"{}".format(receipt_raw[i][1])
        if i > 1:
            if "groceries" not in receipt_data:
                receipt_data["groceries"] = []
            # match if price has been found
            if PRICE_PATTERN.match(receipt_raw[i][1]):
                name = u"{}".format(receipt_raw[i-1][1])
                name.split(" ")[0]
                # name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')
                price = u"{}".format(PRICE_PATTERN.findall(receipt_raw[i][1])[0])
                if '/k' in receipt_raw[i][1]:
                    continue
                receipt_data["groceries"].append([str(name), price])

def write_cache_file(receipt_data: dict) -> None:
    """write to cache file so as to not keep waiting for the ocr system
    """
    if not receipt_data:
        return None
    json_file = os.getcwd() + '/result.json'
    if receipt_data:
        cache_data = read_cache_file()
        if os.path.isfile(json_file):
            os.unlink(json_file) # clear cache
        for r_data in receipt_data:
            cache_data.append(r_data)
        # write this data
        receipt_data = cache_data
    # write new cache
    with open(json_file, 'w', encoding='utf-8') as json_f:
        data = json.dumps(receipt_data, ensure_ascii=False, indent=4)
        json_f.write(data)

def read_cache_file() -> list:
    """read the current json file and return the data dictionary
    """
    json_file_name = os.getcwd() + '/result.json'
    data = []
    if os.path.isfile(json_file_name):
        with open(json_file_name, 'r', encoding='utf-8') as json_f:
            data = json.load(json_f)
    return data

def get_files_from_cache(base_name: Optional[bool]) -> tuple:
    """read the current json file and get the image files from that
    """
    data = read_cache_file()
    file_names = ()
    for d in data:
        if base_name:
            file_names += os.path.basename(d['file_name']),
        else:
            file_names += os.path.normpath(d['file_name']),
    return file_names

def write_to_file(receipt_data: dict) -> None:
    """write to file
    :param receipt_data: <dict> write this receipt data to json file
    """
    if not receipt_data:
        return None
    # writing to csv file
    with open(os.getcwd() + '/result.csv', 'w', newline='', encoding='utf-8') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
        # writing the fields
        csvwriter.writerow(["Item", "Price"])
        for receipt_data in receipt_data:
            # writing the data rows
            csvwriter.writerow(
                ["\n{}".format(receipt_data["file_name"])])
            if "store_location" in receipt_data:
                csvwriter.writerow(["{}".format(receipt_data['store_location'])])
            if "store_name" in receipt_data:
                csvwriter.writerow(["{}".format(receipt_data['store_name'])])
            csvwriter.writerows(receipt_data['groceries'])

if "__main__" == __name__:
    main()
# ________________________________________________________________________
# read_receipt.py
