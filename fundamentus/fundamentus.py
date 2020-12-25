#!/usr/bin/env python3
#
# Fundamentus v2.0
#   as a lib
#   2.0: pandas/DataFrame based
#

import requests
import requests_cache
import pandas   as pd

from tabulate import tabulate


# requests cache: 1h
requests_cache.install_cache('.requests-cache', backend='sqlite', expire_after=3600)


def get_fundamentus_raw(filters={}):
    """
    Get data from fundamentus:
      URL:
        http://fundamentus.com.br/resultado.php

    RAW:
      DataFrame preserves original HTML header names

    Input:
      filters = {}
      list of keys as defined in
      view-source:http://fundamentus.com.br/buscaavancada.php

    Output:
      DataFrame
    """
    ##
    ## Parametros usados em 'Busca avancada por empresa'
    ##   Default: todas as empresas
    ##
    params = {'pl_min'          : '', 'pl_max'          : '',
              'pvp_min'         : '', 'pvp_max'         : '',
              'psr_min'         : '', 'psr_max'         : '',
              'divy_min'        : '', 'divy_max'        : '',
              'pativos_min'     : '', 'pativos_max'     : '',
              'pcapgiro_min'    : '', 'pcapgiro_max'    : '',
              'pebit_min'       : '', 'pebit_max'       : '',
              'fgrah_min'       : '', 'fgrah_max'       : '',
              'firma_ebit_min'  : '', 'firma_ebit_max'  : '',
              'firma_ebitda_min': '', 'firma_ebitda_max': '',
              'margemebit_min'  : '', 'margemebit_max'  : '',
              'margemliq_min'   : '', 'margemliq_max'   : '',
              'liqcorr_min'     : '', 'liqcorr_max'     : '',
              'roic_min'        : '', 'roic_max'        : '',
              'roe_min'         : '', 'roe_max'         : '',
              'liq_min'         : '', 'liq_max'         : '',
              'patrim_min'      : '', 'patrim_max'      : '',
              'divbruta_min'    : '', 'divbruta_max'    : '',
              'tx_cresc_rec_min': '', 'tx_cresc_rec_max': '',
              'setor'           : '',
              }

    ## Parametros: aplicando 'meus' filtros
    params.update(filters)

    ##
    ## Busca avançada por empresa
    ##
    url = 'http://www.fundamentus.com.br/resultado.php'
    hdr = {'User-agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201',
           'Accept': 'text/html, text/plain, text/css, text/sgml, */*;q=0.01',
           'Accept-Encoding': 'gzip, deflate',
           }

    with requests_cache.enabled():
        content = requests.post(url, headers=hdr, data=params)

    ## parse + load
    df = pd.read_html(content.text, decimal=",", thousands='.')[0]

    ## Fix: percent string
    _fix_perc(df,'Div.Yield'    )
    _fix_perc(df,'Mrg Ebit'     )
    _fix_perc(df,'Mrg. Líq.'    )
    _fix_perc(df,'ROIC'         )
    _fix_perc(df,'ROE'          )
    _fix_perc(df,'Cresc. Rec.5a')

    ## index by 'Papel', instead of 'int'
    df.index = df['Papel']
    df.drop('Papel', axis='columns', inplace=True)
    df.sort_index(inplace=True)

    ## naming
    df.name = 'Fundamentus: HTML names'
    df.columns.name = 'Multiples'
    df.index.name = 'Papel'

    ## return sorted by 'Papel'
    return df


def _fix_perc(df, column):
    """
    Fix percent:
      - inplace: replace string in pt-br
      - from '45,56%' to '0.4556'

    Input: DataFrame, column_name
    """

    df[column] = df[column].str.rstrip('%')
    df[column] = df[column].str.replace('.', '' )
    df[column] = df[column].str.replace(',', '.')
    df[column] = df[column].astype(float) / 100

    return


def get_fundamentus(filters={}):
    """
    Get data from fundamentus.
      URL:
        http://fundamentus.com.br/resultado.php

      DataFrame uses short header names

    Input:
      filters = {}

    Output:
      DataFrame
    """

    ## get RAW data
    data1 = get_fundamentus_raw(filters)

    ## rename!
    data2 = _rename_cols(data1)

    ## metadata
    data2.name = 'Fundamentus: short names'
    data2.columns.name = 'Multiples'
    data2.index.name = 'Papel'

    ## remove duplicates
#   df = data2.drop_duplicates(subset=['cotacao','pl','pvp'], keep='last')
    df = data2.drop_duplicates(keep='first')

    return df


def _rename_cols(data):
    """
    Rename columns in DataFrame
      - use a valid Python identifier
      - so each column can be a DataFrame property
      - Example:
          df.pl > 0
    """

    df2 = pd.DataFrame()

    ## Fix: rename columns
    df2['cotacao'  ] = data['Cotação'          ]
    df2['pl'       ] = data['P/L'              ]
    df2['pvp'      ] = data['P/VP'             ]
    df2['psr'      ] = data['PSR'              ]
    df2['dy'       ] = data['Div.Yield'        ]
    df2['pa'       ] = data['P/Ativo'          ]
    df2['pcg'      ] = data['P/Cap.Giro'       ]
    df2['pebit'    ] = data['P/EBIT'           ]
    df2['pacl'     ] = data['P/Ativ Circ.Liq'  ]
    df2['evebit'   ] = data['EV/EBIT'          ]
    df2['evebitda' ] = data['EV/EBITDA'        ]
    df2['mrgebit'  ] = data['Mrg Ebit'         ]
    df2['mrgliq'   ] = data['Mrg. Líq.'        ]
    df2['roic'     ] = data['ROIC'             ]
    df2['roe'      ] = data['ROE'              ]
    df2['liqc'     ] = data['Liq. Corr.'       ]
    df2['liq2m'    ] = data['Liq.2meses'       ]
    df2['patrliq'  ] = data['Patrim. Líq'      ]
    df2['divbpatr' ] = data['Dív.Brut/ Patrim.']
    df2['c5y'      ] = data['Cresc. Rec.5a'    ]

    return df2


##
def print_csv(data):
    """
    CSV printed to stdout
    """
    print(data.to_csv( index=True
                     , header=True
                     , decimal='.'
                     , float_format='%.4f'
                     )
         )

    return


def print_table(data):
    """
    Text table printed to stdout
      - separator: '|'
      - fixed-width columns for better reading
    """
    print( tabulate ( data
                    , headers=data.columns
                    , tablefmt='presto'
                    , floatfmt=".4f"
                    , disable_numparse=False
               )
     )

    return


if __name__ == '__main__':

    data = get_fundamentus()
    print_csv(data)


