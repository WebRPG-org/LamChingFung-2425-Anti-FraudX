"""
香港真實機構名稱和熱線資料庫
用於增強詐騙模擬的真實性和專家建議的可信度
"""

# ============================================================================
# 執法機構
# ============================================================================

LAW_ENFORCEMENT = {
    "香港警務處": {
        "英文名": "Hong Kong Police Force",
        "總部地址": "香港灣仔軍器廠街1號警察總部",
        "緊急熱線": "999",
        "一般查詢": "2860 2000",
        "反詐騙協調中心": {
            "熱線": "2860 5012",
            "防騙易熱線": "18222",
            "網址": "https://www.police.gov.hk/ppp_tc/04_crime_matters/tcd/",
            "電郵": "adcc@police.gov.hk"
        },
        "網絡安全及科技罪案調查科": {
            "熱線": "2860 5012",
            "網址": "https://www.police.gov.hk/ppp_tc/04_crime_matters/tcd/"
        },
        "商業罪案調查科": {
            "熱線": "2860 5012"
        }
    },
    
    "廉政公署": {
        "英文名": "Independent Commission Against Corruption (ICAC)",
        "舉報熱線": "2526 6366",
        "24小時熱線": "25266366",
        "網址": "https://www.icac.org.hk",
        "地址": "香港北角渣華道303號"
    },
    
    "海關": {
        "英文名": "Customs and Excise Department",
        "24小時熱線": "2815 7711",
        "舉報熱線": "2545 6182",
        "網址": "https://www.customs.gov.hk"
    }
}


# ============================================================================
# 金融監管機構
# ============================================================================

FINANCIAL_REGULATORS = {
    "證券及期貨事務監察委員會": {
        "簡稱": "證監會",
        "英文名": "Securities and Futures Commission (SFC)",
        "投資者熱線": "2231 1222",
        "查詢熱線": "2231 1222",
        "網址": "https://www.sfc.hk",
        "地址": "香港中環夏慤道12號美國銀行中心54樓",
        "持牌人及註冊機構查詢": "https://apps.sfc.hk/publicregWeb/",
        "無牌活動舉報": "2231 1222"
    },
    
    "香港金融管理局": {
        "簡稱": "金管局",
        "英文名": "Hong Kong Monetary Authority (HKMA)",
        "查詢熱線": "2878 8222",
        "銀行投訴熱線": "2878 1011",
        "網址": "https://www.hkma.gov.hk",
        "地址": "香港中環金融街8號國際金融中心二期55樓"
    },
    
    "保險業監管局": {
        "簡稱": "保監局",
        "英文名": "Insurance Authority (IA)",
        "查詢熱線": "2520 1868",
        "投訴熱線": "2520 1868",
        "網址": "https://www.ia.org.hk",
        "地址": "香港金鐘道89號力寶中心第一座18樓"
    },
    
    "強制性公積金計劃管理局": {
        "簡稱": "積金局",
        "英文名": "Mandatory Provident Fund Schemes Authority (MPFA)",
        "熱線": "2918 0102",
        "網址": "https://www.mpfa.org.hk",
        "地址": "香港葵涌葵昌路51號九龍貿易中心第2座15樓"
    }
}


# ============================================================================
# 銀行及金融機構
# ============================================================================

BANKS = {
    "香港銀行公會": {
        "英文名": "The Hong Kong Association of Banks",
        "熱線": "2780 1222",
        "網址": "https://www.hkab.org.hk"
    },
    
    "主要銀行": {
        "滙豐銀行": {
            "英文名": "HSBC",
            "客戶服務": "2233 3000",
            "信用卡": "2748 8033",
            "網址": "https://www.hsbc.com.hk"
        },
        "恒生銀行": {
            "英文名": "Hang Seng Bank",
            "客戶服務": "2822 0228",
            "信用卡": "2998 6828",
            "網址": "https://www.hangseng.com"
        },
        "中國銀行(香港)": {
            "英文名": "Bank of China (Hong Kong)",
            "客戶服務": "3988 2388",
            "信用卡": "2853 8828",
            "網址": "https://www.bochk.com"
        },
        "渣打銀行": {
            "英文名": "Standard Chartered Bank",
            "客戶服務": "2886 8868",
            "信用卡": "2886 4111",
            "網址": "https://www.sc.com/hk"
        },
        "東亞銀行": {
            "英文名": "Bank of East Asia",
            "客戶服務": "2211 1333",
            "信用卡": "2211 1388",
            "網址": "https://www.hkbea.com"
        },
        "花旗銀行": {
            "英文名": "Citibank",
            "客戶服務": "2860 0333",
            "信用卡": "2860 0360",
            "網址": "https://www.citibank.com.hk"
        }
    }
}


# ============================================================================
# 消費者保護機構
# ============================================================================

CONSUMER_PROTECTION = {
    "消費者委員會": {
        "簡稱": "消委會",
        "英文名": "Consumer Council",
        "熱線": "2929 2222",
        "投訴熱線": "2929 2222",
        "網址": "https://www.consumer.org.hk",
        "地址": "香港北角渣華道191號嘉華國際中心22樓"
    },
    
    "競爭事務委員會": {
        "簡稱": "競委會",
        "英文名": "Competition Commission",
        "熱線": "3462 2118",
        "網址": "https://www.compcomm.hk"
    }
}


# ============================================================================
# 通訊及科技監管機構
# ============================================================================

TELECOM_REGULATORS = {
    "通訊事務管理局辦公室": {
        "簡稱": "通訊辦",
        "英文名": "Office of the Communications Authority (OFCA)",
        "熱線": "2961 6333",
        "投訴熱線": "2961 6333",
        "網址": "https://www.ofca.gov.hk",
        "地址": "香港灣仔皇后大道東213號胡忠大廈29樓"
    },
    
    "個人資料私隱專員公署": {
        "簡稱": "私隱專員公署",
        "英文名": "Office of the Privacy Commissioner for Personal Data",
        "熱線": "2827 2827",
        "投訴熱線": "2827 2827",
        "網址": "https://www.pcpd.org.hk",
        "地址": "香港灣仔皇后大道東248號大新金融中心12樓"
    },
    
    "政府資訊科技總監辦公室": {
        "簡稱": "資科辦",
        "英文名": "Office of the Government Chief Information Officer (OGCIO)",
        "智方便熱線": "182 123",
        "網址": "https://www.ogcio.gov.hk"
    }
}


# ============================================================================
# 社會福利機構
# ============================================================================

SOCIAL_WELFARE = {
    "社會福利署": {
        "簡稱": "社署",
        "英文名": "Social Welfare Department",
        "熱線": "2343 2255",
        "24小時熱線": "2343 2255",
        "網址": "https://www.swd.gov.hk"
    },
    
    "明愛向晴軒": {
        "英文名": "Caritas Family Crisis Support Centre",
        "24小時熱線": "18288",
        "服務": "危機介入及支援服務"
    },
    
    "香港撒瑪利亞防止自殺會": {
        "英文名": "The Samaritan Befrienders Hong Kong",
        "24小時熱線": "2389 2222"
    }
}


# ============================================================================
# 其他政府部門
# ============================================================================

GOVERNMENT_DEPARTMENTS = {
    "入境事務處": {
        "英文名": "Immigration Department",
        "查詢熱線": "2824 6111",
        "24小時熱線": "2598 0888",
        "網址": "https://www.immd.gov.hk"
    },
    
    "運輸署": {
        "英文名": "Transport Department",
        "查詢熱線": "2804 2600",
        "網址": "https://www.td.gov.hk"
    },
    
    "衞生署": {
        "英文名": "Department of Health",
        "查詢熱線": "2961 8989",
        "網址": "https://www.dh.gov.hk"
    },
    
    "勞工處": {
        "英文名": "Labour Department",
        "查詢熱線": "2717 1771",
        "網址": "https://www.labour.gov.hk"
    },
    
    "稅務局": {
        "英文名": "Inland Revenue Department",
        "查詢熱線": "187 8088",
        "網址": "https://www.ird.gov.hk"
    }
}


# ============================================================================
# 電訊公司
# ============================================================================

TELECOM_COMPANIES = {
    "香港電訊": {
        "英文名": "HKT",
        "客戶服務": "1000",
        "網址": "https://www.hkt.com"
    },
    
    "中國移動香港": {
        "英文名": "China Mobile Hong Kong",
        "客戶服務": "2945 8888",
        "網址": "https://www.hk.chinamobile.com"
    },
    
    "3香港": {
        "英文名": "3 Hong Kong",
        "客戶服務": "3166 3333",
        "網址": "https://www.three.com.hk"
    },
    
    "數碼通": {
        "英文名": "SmarTone",
        "客戶服務": "2880 2688",
        "網址": "https://www.smartone.com"
    },
    
    "中國聯通香港": {
        "英文名": "China Unicom Hong Kong",
        "客戶服務": "1010",
        "網址": "https://www.cuniq.com"
    }
}


# ============================================================================
# 快遞及物流公司
# ============================================================================

COURIER_COMPANIES = {
    "香港郵政": {
        "英文名": "Hongkong Post",
        "客戶服務": "2921 2222",
        "網址": "https://www.hongkongpost.hk"
    },
    
    "順豐速運": {
        "英文名": "SF Express",
        "客戶服務": "2730 0273",
        "網址": "https://www.sf-express.com/hk"
    },
    
    "DHL": {
        "客戶服務": "2400 3388",
        "網址": "https://www.dhl.com/hk"
    },
    
    "FedEx": {
        "客戶服務": "2730 3333",
        "網址": "https://www.fedex.com/hk"
    }
}


# ============================================================================
# 公用事業公司
# ============================================================================

UTILITIES = {
    "中華電力": {
        "英文名": "CLP Power",
        "客戶服務": "2678 2678",
        "網址": "https://www.clp.com.hk"
    },
    
    "香港電燈": {
        "英文名": "HK Electric",
        "客戶服務": "2887 3411",
        "網址": "https://www.hkelectric.com"
    },
    
    "煤氣公司": {
        "英文名": "Towngas",
        "客戶服務": "2880 6988",
        "網址": "https://www.towngas.com"
    },
    
    "水務署": {
        "英文名": "Water Supplies Department",
        "客戶服務": "2824 5000",
        "網址": "https://www.wsd.gov.hk"
    }
}


# ============================================================================
# 交通機構
# ============================================================================

TRANSPORT = {
    "港鐵": {
        "英文名": "MTR",
        "客戶服務": "2881 8888",
        "網址": "https://www.mtr.com.hk"
    },
    
    "九巴": {
        "英文名": "KMB",
        "客戶服務": "2745 4466",
        "網址": "https://www.kmb.hk"
    },
    
    "城巴": {
        "英文名": "Citybus",
        "客戶服務": "2873 0818",
        "網址": "https://www.citybus.com.hk"
    },
    
    "新巴": {
        "英文名": "New World First Bus",
        "客戶服務": "2136 8888",
        "網址": "https://www.nwstbus.com.hk"
    }
}


# ============================================================================
# 網購平台及電商
# ============================================================================

ECOMMERCE_PLATFORMS = {
    "淘寶": {
        "英文名": "Taobao",
        "客戶服務": "內地 400-800-8888",
        "網址": "https://www.taobao.com",
        "警告": "小心假冒淘寶客服，真正的淘寶不會要求你在平台外轉帳"
    },
    
    "天貓": {
        "英文名": "Tmall",
        "客戶服務": "內地 400-860-8608",
        "網址": "https://www.tmall.com",
        "警告": "天貓不會透過電話要求你提供支付密碼"
    },
    
    "京東": {
        "英文名": "JD.com",
        "客戶服務": "內地 950618",
        "網址": "https://www.jd.com"
    },
    
    "HKTVmall": {
        "客戶服務": "2888 7000",
        "網址": "https://www.hktvmall.com"
    },
    
    "Carousell": {
        "網址": "https://www.carousell.com.hk",
        "警告": "使用平台內的付款系統，不要私下轉帳"
    }
}


# ============================================================================
# 支付平台
# ============================================================================

PAYMENT_PLATFORMS = {
    "PayMe": {
        "提供者": "滙豐銀行",
        "客戶服務": "2233 3000",
        "網址": "https://payme.hsbc.com.hk",
        "警告": "PayMe 不會主動致電要求你提供密碼"
    },
    
    "轉數快 (FPS)": {
        "英文名": "Faster Payment System",
        "提供者": "香港金融管理局",
        "查詢": "2878 8222",
        "網址": "https://www.fps.hk",
        "警告": "轉數快是即時轉帳，轉錯帳很難追回"
    },
    
    "支付寶 (香港)": {
        "英文名": "AlipayHK",
        "客戶服務": "2245 3201",
        "網址": "https://www.alipayhk.com",
        "警告": "支付寶不會要求你提供驗證碼或密碼"
    },
    
    "WeChat Pay": {
        "英文名": "微信支付",
        "客戶服務": "內地 95017",
        "網址": "https://pay.weixin.qq.com"
    },
    
    "八達通": {
        "英文名": "Octopus",
        "客戶服務": "2266 2222",
        "網址": "https://www.octopus.com.hk"
    }
}


# ============================================================================
# 投資及證券公司（常被冒充）
# ============================================================================

INVESTMENT_FIRMS = {
    "耀才證券": {
        "英文名": "Bright Smart Securities",
        "客戶服務": "2277 6555",
        "網址": "https://www.bsgroup.com.hk"
    },
    
    "富途證券": {
        "英文名": "Futu Securities",
        "客戶服務": "3719 9895",
        "網址": "https://www.futunn.com"
    },
    
    "盈透證券": {
        "英文名": "Interactive Brokers",
        "客戶服務": "+852 2156 7907",
        "網址": "https://www.interactivebrokers.com.hk"
    },
    
    "警告": "投資前必須在證監會網站查證公司是否持牌：https://apps.sfc.hk/publicregWeb/"
}


# ============================================================================
# 虛擬貨幣交易平台（高風險）
# ============================================================================

CRYPTO_EXCHANGES = {
    "警告": "香港證監會要求虛擬資產交易平台必須領牌，投資前必須查證",
    
    "合法持牌平台查詢": {
        "網址": "https://www.sfc.hk/zh/Regulatory-functions/Intermediaries/Licensing/Register-of-licensed-persons-and-registered-institutions",
        "證監會熱線": "2231 1222"
    },
    
    "常見詐騙特徵": [
        "保證高回報（如每日1-5%）",
        "要求先入金才能提款",
        "無法提款或提款需要額外費用",
        "平台網址經常更換",
        "沒有在證監會註冊"
    ]
}


# ============================================================================
# 社交媒體及通訊平台
# ============================================================================

SOCIAL_MEDIA = {
    "Facebook": {
        "舉報": "https://www.facebook.com/help",
        "警告": "小心 Facebook 上的投資廣告和交友詐騙"
    },
    
    "Instagram": {
        "舉報": "https://help.instagram.com",
        "警告": "小心假冒名人或網紅的投資推薦"
    },
    
    "WhatsApp": {
        "客戶服務": "無官方電話（只能透過 App 內求助）",
        "警告": "WhatsApp 不會主動致電，小心假冒客服"
    },
    
    "Telegram": {
        "警告": "小心投資群組和假冒客服，Telegram 沒有官方客服電話"
    },
    
    "小紅書": {
        "英文名": "Xiaohongshu",
        "警告": "小心租屋詐騙和假代購"
    }
}


# ============================================================================
# 求職平台
# ============================================================================

JOB_PLATFORMS = {
    "JobsDB": {
        "網址": "https://hk.jobsdb.com",
        "客戶服務": "2732 8800"
    },
    
    "CTgoodjobs": {
        "網址": "https://www.ctgoodjobs.hk",
        "客戶服務": "2798 2789"
    },
    
    "Indeed": {
        "網址": "https://hk.indeed.com"
    },
    
    "LinkedIn": {
        "網址": "https://www.linkedin.com"
    },
    
    "勞工處互動就業服務": {
        "網址": "https://www1.jobs.gov.hk",
        "查詢": "2717 1771",
        "警告": "正規公司不會要求求職者先付費或提供銀行帳戶"
    }
}


# ============================================================================
# 票務平台（演唱會詐騙）
# ============================================================================

TICKETING_PLATFORMS = {
    "快達票": {
        "英文名": "KKTIX",
        "網址": "https://kktix.com"
    },
    
    "Cityline": {
        "客戶服務": "2111 5333",
        "網址": "https://www.cityline.com"
    },
    
    "HK Ticketing": {
        "客戶服務": "3128 8288",
        "網址": "https://www.hkticketing.com"
    },
    
    "Klook": {
        "客戶服務": "3462 8668",
        "網址": "https://www.klook.com"
    },
    
    "警告": "小心社交媒體上的假票，使用官方平台購票"
}


# ============================================================================
# 內地執法機構（常被冒充）
# ============================================================================

MAINLAND_AUTHORITIES = {
    "警告": "內地執法機構不會直接致電香港市民",
    
    "常被冒充的機構": [
        "深圳市公安局",
        "廣州市公安局",
        "北京市公安局",
        "上海市公安局",
        "國家安全部",
        "最高人民檢察院",
        "最高人民法院"
    ],
    
    "詐騙特徵": [
        "聲稱你在內地涉案",
        "要求你配合調查",
        "要求你轉帳到「安全帳戶」",
        "威脅會凍結你的帳戶",
        "要求你保密，不要告訴家人"
    ],
    
    "正確做法": "如真的在內地涉案，內地公安會透過香港警方聯絡你，不會直接致電"
}


# ============================================================================
# 租屋相關機構
# ============================================================================

PROPERTY_AGENCIES = {
    "地產代理監管局": {
        "英文名": "Estate Agents Authority (EAA)",
        "查詢熱線": "2111 2777",
        "網址": "https://www.eaa.org.hk",
        "持牌人查詢": "https://www.eaa.org.hk/zh-hk/Information-Centre/Register-of-Licensees"
    },
    
    "差餉物業估價署": {
        "英文名": "Rating and Valuation Department",
        "查詢熱線": "2152 0111",
        "網址": "https://www.rvd.gov.hk",
        "物業查冊": "可查證業主身份"
    },
    
    "土地註冊處": {
        "英文名": "Land Registry",
        "查詢熱線": "3105 0000",
        "網址": "https://www.landreg.gov.hk",
        "物業查冊": "可查證業主身份和物業資料"
    },
    
    "警告": [
        "租屋前必須查證業主身份",
        "不要相信只有照片的租盤",
        "必須實地睇樓",
        "不要在未簽約前付款",
        "小心假業主和假租約"
    ]
}


# ============================================================================
# 貸款及財務公司
# ============================================================================

FINANCE_COMPANIES = {
    "放債人註冊處": {
        "查詢熱線": "2867 2890",
        "網址": "https://www.cr.gov.hk/tc/services/money-lenders.htm",
        "持牌人查詢": "可查證財務公司是否持牌"
    },
    
    "警告": [
        "借貸前必須查證財務公司是否持牌",
        "小心「免入息證明」、「免信貸查詢」的貸款廣告",
        "不要將身份證交給財務公司",
        "小心被誘騙申請貸款後被騙去貸款金額",
        "正規財務公司不會要求你先付手續費"
    ],
    
    "求助熱線": {
        "錢家有道": "2842 3838",
        "社會福利署": "2343 2255",
        "明愛向晴軒": "18288"
    }
}


# ============================================================================
# 常見詐騙中被冒充的機構（重點）
# ============================================================================

COMMONLY_IMPERSONATED = {
    "最常被冒充": [
        {
            "機構": "香港警務處",
            "真實熱線": "2860 2000",
            "防騙易熱線": "18222",
            "警告": "警察絕不會透過電話要求提供密碼、驗證碼或轉帳"
        },
        {
            "機構": "入境事務處",
            "真實熱線": "2824 6111",
            "警告": "入境處不會透過電話要求提供個人資料或轉帳"
        },
        {
            "機構": "海關",
            "真實熱線": "2815 7711",
            "警告": "海關不會透過電話要求轉帳或提供銀行資料"
        },
        {
            "機構": "內地公安",
            "警告": "內地執法機構不會直接致電香港市民，更不會要求轉帳"
        },
        {
            "機構": "銀行（滙豐、恒生等）",
            "警告": "銀行絕不會透過電話或短訊要求提供密碼或驗證碼"
        },
        {
            "機構": "快遞公司（順豐、DHL等）",
            "警告": "快遞公司不會要求提供銀行資料或轉帳"
        }
    ]
}


# ============================================================================
# 詐騙手法詳細資料庫（基於真實案例）
# ============================================================================

SCAM_TACTICS_DETAILS = {
    "假冒官員詐騙": {
        "常用開場白": [
            "你好，我係香港警務處反詐騙組嘅警員",
            "我係入境事務處嘅職員，你嘅身份證涉及一宗案件",
            "我係海關人員，你有包裹被扣查",
            "我係內地公安，你在深圳涉及一宗刑事案件"
        ],
        "常用話術": [
            "你嘅身份證被人盜用",
            "你涉及洗黑錢案件",
            "你嘅帳戶有可疑交易",
            "需要立即配合調查",
            "如果唔配合，會發出拘捕令",
            "要將錢轉到安全帳戶"
        ],
        "真實機構": ["香港警務處", "入境事務處", "海關"],
        "核實方法": "立即掛線，打去機構官方熱線核實",
        "官方熱線": {
            "警務處": "2860 2000",
            "入境處": "2824 6111",
            "海關": "2815 7711",
            "防騙易": "18222"
        }
    },
    
    "假冒銀行詐騙": {
        "常用開場白": [
            "你好，我係XX銀行客戶服務部",
            "你嘅網上理財帳戶出現異常登入",
            "你嘅信用卡有可疑交易",
            "你嘅帳戶需要更新資料"
        ],
        "常用話術": [
            "需要你提供驗證碼確認身份",
            "請提供你嘅網上理財密碼",
            "請點擊短訊內的連結更新資料",
            "如果唔立即處理，帳戶會被凍結"
        ],
        "真實銀行": ["滙豐", "恒生", "中銀", "渣打", "東亞", "花旗"],
        "核實方法": "掛線後打去銀行卡背面的官方熱線",
        "銀行公會熱線": "2780 1222",
        "關鍵警告": "銀行絕不會要求你提供驗證碼或密碼"
    },
    
    "投資詐騙": {
        "常用開場白": [
            "你好，我係XX投資公司嘅理財顧問",
            "我哋有個獨家投資項目",
            "保證每月回報10%",
            "而家有優惠，首次投資免手續費"
        ],
        "常用話術": [
            "保證高回報",
            "低風險高回報",
            "有政府監管",
            "好多客戶都賺咗好多錢",
            "限時優惠，過咗就冇",
            "先入金，之後可以隨時提款"
        ],
        "常見平台": [
            "假虛擬貨幣交易平台",
            "假外匯交易平台",
            "假股票投資平台",
            "假黃金投資平台"
        ],
        "核實方法": "在證監會網站查證公司是否持牌",
        "證監會熱線": "2231 1222",
        "查牌網址": "https://apps.sfc.hk/publicregWeb/",
        "關鍵警告": "合法投資公司不會保證回報"
    },
    
    "網購詐騙": {
        "常見平台": ["Facebook", "Instagram", "Carousell", "小紅書"],
        "常見貨品": ["演唱會門票", "限量波鞋", "名牌手袋", "電子產品", "口罩"],
        "詐騙特徵": [
            "價格明顯低於市價",
            "只接受銀行轉帳或轉數快",
            "不使用平台內的付款系統",
            "要求先付全款",
            "賣家資料不全",
            "付款後無法聯絡賣家"
        ],
        "核實方法": "使用「防騙視伏器」評估風險",
        "防騙視伏器": "https://cyberdefender.hk",
        "消委會熱線": "2929 2222"
    },
    
    "求職詐騙": {
        "常見招聘": [
            "點讚員",
            "下單員",
            "數據輸入員",
            "在家工作",
            "兼職打字員"
        ],
        "詐騙特徵": [
            "不需要學歷經驗",
            "高薪厚職",
            "在家工作",
            "要求先付保證金或培訓費",
            "要求提供銀行帳戶申請貸款"
        ],
        "核實方法": "在勞工處網站查證公司",
        "勞工處熱線": "2717 1771",
        "關鍵警告": "正規公司不會要求求職者先付費"
    },
    
    "愛情詐騙": {
        "常見平台": ["交友App", "Facebook", "Instagram", "WhatsApp"],
        "騙徒特徵": [
            "自稱高富帥或白富美",
            "快速建立戀愛關係",
            "從未見面或視像通話",
            "經常在外地工作",
            "聲稱懂得投資"
        ],
        "詐騙手法": [
            "游說投資虛擬貨幣",
            "聲稱遇到困難需要借錢",
            "要求幫忙收款或轉帳",
            "邀請一起投資"
        ],
        "關鍵警告": "網上戀人要求金錢往來，必定是騙局"
    },
    
    "租屋詐騙": {
        "常見平台": ["小紅書", "Facebook", "Instagram"],
        "詐騙特徵": [
            "租金明顯低於市價",
            "只有照片，不能實地睇樓",
            "業主在外地，不能見面",
            "要求先付按金或租金",
            "提供假租約和假身份證"
        ],
        "核實方法": [
            "在土地註冊處查冊核實業主身份",
            "要求實地睇樓",
            "查證地產代理是否持牌"
        ],
        "地產代理監管局": "2111 2777",
        "土地註冊處": "3105 0000"
    },
    
    "電話騙案（改號電話）": {
        "特徵": "來電顯示 +852 開頭",
        "警告": "+852 開頭的來電可能是改號電話",
        "常被冒充": [
            "政府部門",
            "銀行",
            "快遞公司",
            "電訊公司"
        ],
        "核實方法": "掛線後用自己的電話打去官方熱線核實"
    }
}


# ============================================================================
# 實用查詢工具
# ============================================================================

VERIFICATION_TOOLS = {
    "防騙視伏器": {
        "網址": "https://cyberdefender.hk",
        "功能": "評估網購風險、檢查可疑網站",
        "提供者": "香港警務處"
    },
    
    "持牌人及註冊機構查詢": {
        "網址": "https://apps.sfc.hk/publicregWeb/",
        "功能": "查證投資公司是否在證監會註冊",
        "提供者": "證監會"
    },
    
    "認可機構名單": {
        "網址": "https://www.hkma.gov.hk/chi/key-functions/banking-stability/banking-policy-and-supervision/list-of-ais/",
        "功能": "查證銀行是否受金管局監管",
        "提供者": "金管局"
    },
    
    "保險公司登記冊": {
        "網址": "https://www.ia.org.hk/tc/legislative_framework/reg_of_insurers.html",
        "功能": "查證保險公司是否受保監局監管",
        "提供者": "保監局"
    }
}


# ============================================================================
# 輔助函數
# ============================================================================

def get_official_hotline(organization_name: str) -> dict:
    """
    獲取機構的官方熱線
    
    Args:
        organization_name: 機構名稱（中文或英文）
    
    Returns:
        dict: 包含熱線和網址的字典
    """
    # 搜索所有類別
    all_orgs = {
        **LAW_ENFORCEMENT,
        **FINANCIAL_REGULATORS,
        **CONSUMER_PROTECTION,
        **TELECOM_REGULATORS,
        **SOCIAL_WELFARE,
        **GOVERNMENT_DEPARTMENTS
    }
    
    for org_name, org_data in all_orgs.items():
        if organization_name in org_name or organization_name in org_data.get("英文名", ""):
            return {
                "機構": org_name,
                "熱線": org_data.get("熱線") or org_data.get("查詢熱線") or org_data.get("客戶服務"),
                "網址": org_data.get("網址", ""),
                "地址": org_data.get("地址", "")
            }
    
    return {"error": "找不到該機構"}


def get_bank_hotline(bank_name: str) -> dict:
    """獲取銀行的官方熱線"""
    banks = BANKS.get("主要銀行", {})
    
    for name, data in banks.items():
        if bank_name in name or bank_name in data.get("英文名", ""):
            return {
                "銀行": name,
                "客戶服務": data.get("客戶服務"),
                "信用卡": data.get("信用卡"),
                "網址": data.get("網址")
            }
    
    return {"error": "找不到該銀行"}


def get_anti_scam_hotlines() -> list:
    """獲取所有防詐騙相關熱線"""
    return [
        {"名稱": "防騙易熱線", "熱線": "18222", "機構": "香港警務處"},
        {"名稱": "反詐騙協調中心", "熱線": "2860 5012", "機構": "香港警務處"},
        {"名稱": "證監會投資者熱線", "熱線": "2231 1222", "機構": "證監會"},
        {"名稱": "銀行公會熱線", "熱線": "2780 1222", "機構": "香港銀行公會"},
        {"名稱": "消委會熱線", "熱線": "2929 2222", "機構": "消費者委員會"},
        {"名稱": "通訊辦熱線", "熱線": "2961 6333", "機構": "通訊事務管理局辦公室"}
    ]


def get_scam_tactic_details(scam_type: str) -> dict:
    """
    獲取詐騙手法的詳細資料
    
    Args:
        scam_type: 詐騙類型
    
    Returns:
        dict: 詐騙手法的詳細資料
    """
    return SCAM_TACTICS_DETAILS.get(scam_type, {})


def get_scammer_opening_lines(scam_type: str) -> list:
    """
    獲取騙徒的常用開場白
    
    Args:
        scam_type: 詐騙類型
    
    Returns:
        list: 開場白列表
    """
    details = SCAM_TACTICS_DETAILS.get(scam_type, {})
    return details.get("常用開場白", [])


def get_scammer_tactics(scam_type: str) -> list:
    """
    獲取騙徒的常用話術
    
    Args:
        scam_type: 詐騙類型
    
    Returns:
        list: 話術列表
    """
    details = SCAM_TACTICS_DETAILS.get(scam_type, {})
    return details.get("常用話術", [])


def get_verification_method(scam_type: str) -> str:
    """
    獲取核實方法
    
    Args:
        scam_type: 詐騙類型
    
    Returns:
        str: 核實方法說明
    """
    details = SCAM_TACTICS_DETAILS.get(scam_type, {})
    return details.get("核實方法", "如有懷疑，打去防騙易熱線 18222")


def format_for_expert_response(scam_type: str) -> str:
    """
    根據詐騙類型，格式化專家應該提供的官方熱線
    
    Args:
        scam_type: 詐騙類型（假冒官員/假冒銀行/投資詐騙等）
    
    Returns:
        str: 格式化的建議文字
    """
    if "假冒官員" in scam_type or "警察" in scam_type:
        return """
立即掛線，如果你唔放心，可以打去以下官方熱線核實：
- 警務處查詢熱線：2860 2000
- 防騙易熱線：18222
記住，真正嘅警務人員絕不會透過電話要求你提供密碼或轉帳。
"""
    
    elif "假冒銀行" in scam_type or "銀行" in scam_type:
        return """
立即掛線，唔好提供任何驗證碼。如果你唔放心，可以：
1. 打去你銀行嘅官方熱線（印喺你張提款卡背面）
2. 或者打去銀行公會熱線：2780 1222
記住，銀行絕不會透過電話或短訊要求你提供驗證碼。
"""
    
    elif "投資" in scam_type:
        return """
唔好立即投資！先做以下核實：
1. 打去證監會投資者熱線：2231 1222
2. 上證監會網站查證公司是否持牌：https://apps.sfc.hk/publicregWeb/
3. 記住，合法投資公司唔會保證回報
如有懷疑，打去防騙易熱線：18222
"""
    
    elif "網購" in scam_type:
        return """
唔好立即付款！先做以下檢查：
1. 用「防騙視伏器」評估風險：https://cyberdefender.hk
2. 檢查賣家評價和交易記錄
3. 使用有保障嘅付款方式（如信用卡、PayPal）
如有懷疑，打去防騙易熱線：18222 或消委會：2929 2222
"""
    
    elif "求職" in scam_type:
        return """
小心求職陷阱！正規公司不會：
1. 要求求職者先付費
2. 要求提供銀行帳戶申請貸款
3. 承諾「不需經驗、高薪厚職」
如有懷疑，打去勞工處熱線：2717 1771 或防騙易熱線：18222
"""
    
    elif "愛情" in scam_type or "交友" in scam_type:
        return """
小心網上情緣騙案！如果對方：
1. 從未見面或視像通話
2. 要求金錢往來
3. 游說你投資
呢個必定係騙局！打去防騙易熱線：18222 求助。
"""
    
    elif "租屋" in scam_type:
        return """
租屋前必須做以下核實：
1. 在土地註冊處查冊核實業主身份（熱線：3105 0000）
2. 實地睇樓，唔好只睇相片
3. 查證地產代理是否持牌（地監局：2111 2777）
如有懷疑，打去防騙易熱線：18222
"""
    
    else:
        return """
如有懷疑，立即掛線並打去以下熱線核實：
- 防騙易熱線：18222
- 警務處查詢熱線：2860 2000
記住，任何要求你立即轉帳或提供密碼嘅來電，都好可能係騙局。
"""


def generate_scammer_context(scam_type: str) -> str:
    """
    為騙徒 Agent 生成上下文資料
    
    Args:
        scam_type: 詐騙類型
    
    Returns:
        str: 格式化的上下文資料
    """
    details = get_scam_tactic_details(scam_type)
    
    if not details:
        return f"你正在模擬「{scam_type}」詐騙手法。"
    
    context = f"## 詐騙手法：{scam_type}\n\n"
    
    if "常用開場白" in details:
        context += "### 常用開場白（選擇其中一個）\n"
        for line in details["常用開場白"]:
            context += f"- {line}\n"
        context += "\n"
    
    if "常用話術" in details:
        context += "### 常用話術（根據情況使用）\n"
        for tactic in details["常用話術"]:
            context += f"- {tactic}\n"
        context += "\n"
    
    if "真實機構" in details:
        context += f"### 可冒充的真實機構\n"
        for org in details["真實機構"]:
            context += f"- {org}\n"
        context += "\n"
    
    return context


def generate_expert_context(scam_type: str) -> str:
    """
    為專家 Agent 生成上下文資料
    
    Args:
        scam_type: 詐騙類型
    
    Returns:
        str: 格式化的上下文資料
    """
    details = get_scam_tactic_details(scam_type)
    
    if not details:
        return format_for_expert_response(scam_type)
    
    context = f"## 你正在處理：{scam_type}\n\n"
    
    if "核實方法" in details:
        context += f"### 核實方法\n{details['核實方法']}\n\n"
    
    if "官方熱線" in details:
        context += "### 官方熱線\n"
        for org, hotline in details["官方熱線"].items():
            context += f"- {org}：{hotline}\n"
        context += "\n"
    
    if "關鍵警告" in details:
        context += f"### 關鍵警告\n{details['關鍵警告']}\n\n"
    
    context += "### 你的建議\n"
    context += format_for_expert_response(scam_type)
    
    return context


# ============================================================================
# 導出所有資料
# ============================================================================

HONG_KONG_ORGANIZATIONS = {
    "執法機構": LAW_ENFORCEMENT,
    "金融監管機構": FINANCIAL_REGULATORS,
    "銀行": BANKS,
    "消費者保護": CONSUMER_PROTECTION,
    "通訊科技監管": TELECOM_REGULATORS,
    "社會福利": SOCIAL_WELFARE,
    "政府部門": GOVERNMENT_DEPARTMENTS,
    "電訊公司": TELECOM_COMPANIES,
    "快遞物流": COURIER_COMPANIES,
    "公用事業": UTILITIES,
    "交通機構": TRANSPORT,
    "網購平台": ECOMMERCE_PLATFORMS,
    "支付平台": PAYMENT_PLATFORMS,
    "投資證券": INVESTMENT_FIRMS,
    "虛擬貨幣": CRYPTO_EXCHANGES,
    "社交媒體": SOCIAL_MEDIA,
    "求職平台": JOB_PLATFORMS,
    "票務平台": TICKETING_PLATFORMS,
    "內地機構": MAINLAND_AUTHORITIES,
    "租屋相關": PROPERTY_AGENCIES,
    "貸款財務": FINANCE_COMPANIES,
    "常被冒充機構": COMMONLY_IMPERSONATED,
    "詐騙手法詳情": SCAM_TACTICS_DETAILS,
    "查詢工具": VERIFICATION_TOOLS
}


if __name__ == "__main__":
    # 測試
    print("=" * 60)
    print("香港真實機構資料庫測試")
    print("=" * 60)
    
    print("\n[1] 防詐騙相關熱線")
    print("-" * 60)
    for hotline in get_anti_scam_hotlines():
        print(f"{hotline['名稱']}: {hotline['熱線']} ({hotline['機構']})")
    
    print("\n[2] 查詢警務處熱線")
    print("-" * 60)
    police_info = get_official_hotline("警務處")
    print(f"機構: {police_info.get('機構')}")
    print(f"熱線: {police_info.get('熱線')}")
    
    print("\n[3] 查詢滙豐銀行熱線")
    print("-" * 60)
    hsbc_info = get_bank_hotline("滙豐")
    print(f"銀行: {hsbc_info.get('銀行')}")
    print(f"客戶服務: {hsbc_info.get('客戶服務')}")
    
    print("\n[4] 假冒官員詐騙 - 騙徒開場白")
    print("-" * 60)
    opening_lines = get_scammer_opening_lines("假冒官員詐騙")
    for i, line in enumerate(opening_lines, 1):
        print(f"{i}. {line}")
    
    print("\n[5] 假冒銀行詐騙 - 專家建議")
    print("-" * 60)
    expert_advice = format_for_expert_response("假冒銀行")
    print(expert_advice)
    
    print("\n[6] 投資詐騙 - 核實方法")
    print("-" * 60)
    verification = get_verification_method("投資詐騙")
    print(verification)
    
    print("\n[7] 生成騙徒上下文（假冒官員）")
    print("-" * 60)
    scammer_context = generate_scammer_context("假冒官員詐騙")
    print(scammer_context[:300] + "...")
    
    print("\n[8] 生成專家上下文（投資詐騙）")
    print("-" * 60)
    expert_context = generate_expert_context("投資詐騙")
    print(expert_context[:300] + "...")
    
    print("\n[9] 資料庫統計")
    print("-" * 60)
    print(f"總類別數: {len(HONG_KONG_ORGANIZATIONS)}")
    print(f"詐騙手法類型: {len(SCAM_TACTICS_DETAILS)}")
    print(f"主要銀行數: {len(BANKS.get('主要銀行', {}))}")
    print(f"電訊公司數: {len(TELECOM_COMPANIES)}")
    print(f"支付平台數: {len(PAYMENT_PLATFORMS)}")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
