from lxml import etree

INFILE = 'currencies.xml'
OUTFILE = 'currency.py'

def convert(infile, outfile):
    doc = etree.parse(infile)
    data = {}
    for currency in doc.findall('//ISO_CURRENCY'):
        code = currency.findtext('ALPHABETIC_CODE')
        if not code:
            continue
        data[code] = currency.findtext('CURRENCY').strip()
    from pprint import pformat
    var = "CURRENCIES = {"
    text = pformat(data, indent=len(var), depth=10)
    pad = " " * (len(var)-1)
    text = text.replace("{" + pad, var)
    fh = open(outfile, 'w')
    fh.write("#coding: utf-8\n\n")
    fh.write(text)
    fh.write("\n\n")
    fh.close()

if __name__ == '__main__':
    convert(INFILE, OUTFILE)
