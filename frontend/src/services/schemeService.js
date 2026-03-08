// Comprehensive scheme database with REAL 2025 data from official sources
// Data sourced from myScheme.gov.in, official government portals, and verified news sources
// Last updated: 2026-03-01 (Real 2025 data with current rates and eligibility)
const mockSchemes = [
  {
    id: "pm-kisan-2025",
    name: "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
    nameEn: "PM-KISAN",
    nameHi: "प्रधानमंत्री किसान सम्मान निधि",
    category: "Agriculture",
    type: "Central",
    ministry: "Ministry of Agriculture & Farmers Welfare",
    description:
      "Direct income support providing ₹6,000 per year to ALL landholding farmer families in three equal installments of ₹2,000 each every four months. 20th installment expected June-July 2025, benefiting 9.8 crore farmers.",
    descriptionHi:
      "सभी भूमिधारक किसान परिवारों को हर चार महीने में ₹2,000 की तीन समान किस्तों में प्रति वर्ष ₹6,000 की प्रत्यक्ष आय सहायता। 20वीं किस्त जून-जुलाई 2025 में अपेक्षित, 9.8 करोड़ किसानों को लाभ।",
    benefits: [
      "₹6,000 per year via Direct Benefit Transfer (DBT) into Aadhaar-seeded bank accounts",
      "20th installment expected June-July 2025",
      "Benefiting approximately 9.8 crore farmers",
      "No middlemen - direct to bank account",
      "Land-holding is the ONLY eligibility criteria",
    ],
    benefitsHi: [
      "आधार-सीडेड बैंक खातों में DBT के माध्यम से प्रति वर्ष ₹6,000",
      "20वीं किस्त जून-जुलाई 2025 में अपेक्षित",
      "लगभग 9.8 करोड़ किसानों को लाभ",
      "कोई बिचौलिया नहीं - सीधे बैंक खाते में",
      "भूमि-धारण ही एकमात्र पात्रता मानदंड है",
    ],
    eligibility: {
      minAge: 18,
      maxAge: 999,
      minIncome: 0,
      maxIncome: 999999999,
      states: ["all"],
      occupation: ["farmer", "agriculture"],
      categories: ["all"],
    },
    documents: [
      "Aadhaar Card",
      "Bank Account Details (Aadhaar-seeded)",
      "Land Ownership Documents",
      "Mobile Number",
    ],
    officialWebsite: "https://pmkisan.gov.in/",
    helpline: "155261 / 011-24300606",
  },
  {
    id: "ayushman-bharat-2025",
    name: "Ayushman Bharat - PM-JAY (Pradhan Mantri Jan Arogya Yojana)",
    nameEn: "Ayushman Bharat PM-JAY",
    nameHi: "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना",
    category: "Healthcare",
    type: "Central",
    ministry: "National Health Authority (NHA)",
    description:
      "World's largest health insurance scheme providing ₹5 lakh per family per year for secondary and tertiary care hospitalization. RECENTLY EXTENDED to ALL senior citizens aged 70+ years regardless of income (2025 update).",
    descriptionHi:
      "द्वितीयक और तृतीयक देखभाल अस्पताल में भर्ती के लिए प्रति परिवार प्रति वर्ष ₹5 लाख प्रदान करने वाली विश्व की सबसे बड़ी स्वास्थ्य बीमा योजना। हाल ही में आय की परवाह किए बिना 70+ वर्ष के सभी वरिष्ठ नागरिकों तक विस्तारित (2025 अपडेट)।",
    benefits: [
      "₹5 lakh health coverage per family per year",
      "Cashless and paperless treatment at empanelled hospitals",
      "Covers 1,949 medical procedures (updated 2025)",
      "Pre and post-hospitalization expenses covered",
      "ALL senior citizens 70+ eligible regardless of income (2025 extension)",
      "Apply online through NHA website or Ayushman app",
    ],
    benefitsHi: [
      "प्रति परिवार प्रति वर्ष ₹5 लाख स्वास्थ्य कवरेज",
      "सूचीबद्ध अस्पतालों में कैशलेस और पेपरलेस उपचार",
      "1,949 चिकित्सा प्रक्रियाओं को कवर करता है (2025 अपडेट)",
      "अस्पताल में भर्ती से पहले और बाद के खर्च कवर",
      "आय की परवाह किए बिना 70+ के सभी वरिष्ठ नागरिक पात्र (2025 विस्तार)",
      "NHA वेबसाइट या आयुष्मान ऐप के माध्यम से ऑनलाइन आवेदन करें",
    ],
    eligibility: {
      minAge: 0,
      maxAge: 999,
      minIncome: 0,
      maxIncome: 999999999,
      states: ["all"],
      occupation: ["all"],
      categories: ["SECC 2011 families", "All Senior Citizens 70+"],
    },
    documents: [
      "Aadhaar Card",
      "Ration Card",
      "Mobile Number",
      "Age Proof (for senior citizens 70+)",
    ],
    officialWebsite: "https://pmjay.gov.in/",
    helpline: "14555",
  },
  {
    id: "pmay-urban-2025",
    name: "PMAY-Urban 2.0 (Pradhan Mantri Awas Yojana - Urban)",
    nameEn: "PMAY-Urban 2.0",
    nameHi: "प्रधानमंत्री आवास योजना - शहरी 2.0",
    category: "Housing",
    type: "Central",
    ministry: "Ministry of Housing & Urban Affairs",
    description:
      "Housing for All scheme providing financial assistance for construction or purchase of houses in urban areas. Phase 2 aims to construct 1 crore houses by 2029. DEADLINE EXTENDED till December 2025.",
    descriptionHi:
      "शहरी क्षेत्रों में घरों के निर्माण या खरीद के लिए वित्तीय सहायता प्रदान करने वाली सभी के लिए आवास योजना। चरण 2 का लक्ष्य 2029 तक 1 करोड़ घर बनाना है। समय सीमा दिसंबर 2025 तक बढ़ाई गई।",
    benefits: [
      "Interest subsidy up to ₹2.67 lakh on home loans",
      "EWS: Up to ₹1.5 lakh direct assistance",
      "LIG: Up to ₹2.67 lakh subsidy",
      "MIG-I (₹6-12 lakh income): Interest subsidy available",
      "MIG-II (₹12-18 lakh income): Interest subsidy available",
      "Registration deadline: December 2025",
    ],
    benefitsHi: [
      "होम लोन पर ₹2.67 लाख तक की ब्याज सब्सिडी",
      "EWS: ₹1.5 लाख तक की प्रत्यक्ष सहायता",
      "LIG: ₹2.67 लाख तक की सब्सिडी",
      "MIG-I (₹6-12 लाख आय): ब्याज सब्सिडी उपलब्ध",
      "MIG-II (₹12-18 लाख आय): ब्याज सब्सिडी उपलब्ध",
      "पंजीकरण की समय सीमा: दिसंबर 2025",
    ],
    eligibility: {
      minAge: 18,
      maxAge: 999,
      minIncome: 0,
      maxIncome: 1800000,
      states: ["all"],
      occupation: ["all"],
      categories: ["EWS", "LIG", "MIG-I", "MIG-II"],
    },
    documents: [
      "Aadhaar Card",
      "Income Certificate",
      "Bank Account Details",
      "Property Documents",
      "Caste Certificate (if applicable)",
    ],
    officialWebsite: "https://pmaymis.gov.in/",
    helpline: "1800-11-6163",
  },
  {
    id: "kisan-credit-card",
    name: "Kisan Credit Card (KCC)",
    nameEn: "Kisan Credit Card",
    nameHi: "किसान क्रेडिट कार्ड",
    category: "Agriculture",
    type: "Central",
    ministry: "Ministry of Agriculture & Farmers Welfare",
    description:
      "Credit facility for farmers at subsidized interest rates for crop cultivation and allied activities",
    descriptionHi:
      "फसल की खेती और संबद्ध गतिविधियों के लिए रियायती ब्याज दरों पर किसानों के लिए ऋण सुविधा",
    benefits: [
      "Interest rate: 4% per annum (after subsidy)",
      "2% interest subvention + 3% prompt repayment incentive",
      "Flexible repayment up to 6 years (2026 update)",
      "Covers crop cultivation, allied activities, post-harvest expenses",
      "Insurance coverage included",
      "Tenant farmers and sharecroppers now eligible (2026)",
    ],
    benefitsHi: [
      "ब्याज दर: 4% प्रति वर्ष (सब्सिडी के बाद)",
      "2% ब्याज छूट + 3% त्वरित पुनर्भुगतान प्रोत्साहन",
      "6 साल तक लचीली पुनर्भुगतान (2026 अपडेट)",
      "फसल की खेती, संबद्ध गतिविधियां, कटाई के बाद के खर्च को कवर करता है",
      "बीमा कवरेज शामिल",
      "किरायेदार किसान और बटाईदार अब पात्र (2026)",
    ],
    eligibility: {
      minAge: 18,
      maxAge: 75,
      minIncome: 0,
      maxIncome: 1000000,
      states: ["all"],
      occupation: ["farmer", "agriculture", "tenant farmer", "sharecropper"],
      categories: ["all"],
    },
    documents: [
      "Aadhaar Card",
      "Land Ownership Documents or Tenancy Agreement",
      "Bank Account Details",
      "Passport Size Photos",
    ],
    officialWebsite: "https://www.rbi.org.in/",
  },
  {
    id: "pmay-gramin",
    name: "PMAY-Gramin (Pradhan Mantri Awas Yojana - Rural)",
    nameEn: "PMAY-Gramin",
    nameHi: "प्रधानमंत्री आवास योजना - ग्रामीण",
    category: "Housing",
    type: "Central",
    ministry: "Ministry of Rural Development",
    description:
      "Housing scheme for rural poor providing financial assistance for construction of pucca houses",
    descriptionHi:
      "पक्के मकान के निर्माण के लिए वित्तीय सहायता प्रदान करने वाली ग्रामीण गरीबों के लिए आवास योजना",
    benefits: [
      "₹1.2 lakh assistance in plains",
      "₹1.3 lakh assistance in hilly/difficult areas",
      "Institutional loan up to ₹70,000 at 3% lower interest",
      "Toilet construction assistance: ₹12,000",
      "90/95 days of unskilled wage employment under MGNREGA",
    ],
    benefitsHi: [
      "मैदानी क्षेत्रों में ₹1.2 लाख सहायता",
      "पहाड़ी/कठिन क्षेत्रों में ₹1.3 लाख सहायता",
      "3% कम ब्याज पर ₹70,000 तक संस्थागत ऋण",
      "शौचालय निर्माण सहायता: ₹12,000",
      "मनरेगा के तहत 90/95 दिनों का अकुशल मजदूरी रोजगार",
    ],
    eligibility: {
      minAge: 18,
      maxAge: 100,
      minIncome: 0,
      maxIncome: 200000,
      states: ["all"],
      occupation: ["all"],
      categories: ["BPL", "SC/ST", "Minorities", "Homeless"],
    },
    documents: [
      "Aadhaar Card",
      "BPL Card",
      "Bank Account Details",
      "Caste Certificate (if applicable)",
      "Income Certificate",
    ],
    officialWebsite: "https://pmayg.nic.in/",
  },
  {
    id: "mudra-yojana",
    name: "Pradhan Mantri MUDRA Yojana",
    nameEn: "PM MUDRA Yojana",
    nameHi: "प्रधानमंत्री मुद्रा योजना",
    category: "Employment",
    type: "Central",
    ministry: "Ministry of Finance",
    description:
      "Provides loans up to ₹10 lakh to non-corporate, non-farm small/micro enterprises",
    descriptionHi:
      "गैर-कॉर्पोरेट, गैर-कृषि लघु/सूक्ष्म उद्यमों को ₹10 लाख तक का ऋण प्रदान करता है",
    benefits: [
      "Shishu: Loans up to ₹50,000",
      "Kishore: Loans from ₹50,001 to ₹5 lakh",
      "Tarun: Loans from ₹5 lakh to ₹10 lakh",
      "No collateral required",
      "Lower interest rates",
    ],
    benefitsHi: [
      "शिशु: ₹50,000 तक का ऋण",
      "किशोर: ₹50,001 से ₹5 लाख तक का ऋण",
      "तरुण: ₹5 लाख से ₹10 लाख तक का ऋण",
      "कोई संपार्श्विक आवश्यक नहीं",
      "कम ब्याज दरें",
    ],
    eligibility: {
      minAge: 18,
      maxAge: 65,
      minIncome: 0,
      maxIncome: 500000,
      states: ["all"],
      occupation: ["self-employed", "small business", "entrepreneur"],
      categories: ["all"],
    },
    documents: [
      "Aadhaar Card",
      "PAN Card",
      "Business Plan",
      "Bank Account Details",
      "Address Proof",
    ],
    officialWebsite: "https://www.mudra.org.in/",
  },
  {
    id: "sukanya-samriddhi-2025",
    name: "Sukanya Samriddhi Yojana (SSY)",
    nameEn: "Sukanya Samriddhi Yojana",
    nameHi: "सुकन्या समृद्धि योजना",
    category: "Women & Child",
    type: "Central",
    ministry: "Ministry of Finance",
    description:
      "Small deposit scheme for girl child under Beti Bachao Beti Padhao campaign with attractive 8.2% interest rate (Q2 FY 2025-26, compounded yearly) and complete tax exemption.",
    descriptionHi:
      "बेटी बचाओ बेटी पढ़ाओ अभियान के तहत बालिकाओं के लिए आकर्षक 8.2% ब्याज दर (Q2 वित्त वर्ष 2025-26, वार्षिक चक्रवृद्धि) और पूर्ण कर छूट के साथ छोटी जमा योजना।",
    benefits: [
      "8.2% interest rate per annum (compounded yearly, Q2 FY 2025-26)",
      "Tax deduction under Section 80C up to ₹1.5 lakh",
      "Minimum deposit: ₹250 per year",
      "Maximum deposit: ₹1.5 lakh per year",
      "Maturity: 21 years from account opening or marriage after 18 years",
      "Partial withdrawal allowed after girl turns 18 (50% for education)",
    ],
    benefitsHi: [
      "8.2% ब्याज दर प्रति वर्ष (वार्षिक चक्रवृद्धि, Q2 वित्त वर्ष 2025-26)",
      "धारा 80C के तहत ₹1.5 लाख तक कर कटौती",
      "न्यूनतम जमा: ₹250 प्रति वर्ष",
      "अधिकतम जमा: ₹1.5 लाख प्रति वर्ष",
      "परिपक्वता: खाता खोलने से 21 वर्ष या 18 वर्ष के बाद विवाह",
      "लड़की के 18 वर्ष की होने के बाद आंशिक निकासी की अनुमति (शिक्षा के लिए 50%)",
    ],
    eligibility: {
      minAge: 0,
      maxAge: 10,
      minIncome: 0,
      maxIncome: 999999999,
      states: ["all"],
      occupation: ["all"],
      categories: ["Girl Child only"],
    },
    documents: [
      "Birth Certificate of Girl Child",
      "Parent's Aadhaar Card",
      "Parent's PAN Card",
      "Address Proof",
      "Passport Size Photos",
    ],
    officialWebsite: "https://www.indiapost.gov.in/",
    helpline: "1800-11-2011",
  },
  {
    id: "atal-pension",
    name: "Atal Pension Yojana",
    nameEn: "Atal Pension Yojana",
    nameHi: "अटल पेंशन योजना",
    category: "Social Security",
    type: "Central",
    ministry: "Ministry of Finance",
    description:
      "Pension scheme for unorganized sector workers providing guaranteed pension after 60 years",
    descriptionHi:
      "असंगठित क्षेत्र के श्रमिकों के लिए पेंशन योजना जो 60 वर्ष के बाद गारंटीड पेंशन प्रदान करती है",
    benefits: [
      "Guaranteed pension: ₹1,000 to ₹5,000 per month",
      "Government co-contribution for eligible subscribers",
      "Spouse pension after subscriber's death",
      "Return of corpus to nominee",
      "Tax benefits under Section 80CCD",
    ],
    benefitsHi: [
      "गारंटीड पेंशन: ₹1,000 से ₹5,000 प्रति माह",
      "पात्र ग्राहकों के लिए सरकारी सह-योगदान",
      "ग्राहक की मृत्यु के बाद पति/पत्नी पेंशन",
      "नामांकित व्यक्ति को कोष की वापसी",
      "धारा 80CCD के तहत कर लाभ",
    ],
    eligibility: {
      minAge: 18,
      maxAge: 40,
      minIncome: 0,
      maxIncome: 500000,
      states: ["all"],
      occupation: ["unorganized sector workers"],
      categories: ["all"],
    },
    documents: ["Aadhaar Card", "Bank Account Details", "Mobile Number"],
    officialWebsite: "https://www.npscra.nsdl.co.in/",
  },
];

// Extract user information from text
export const extractUserInfo = (text) => {
  const info = {
    age: null,
    state: null,
    income: null,
    occupation: null,
  };

  // Extract age
  const ageMatch = text.match(
    /age\s*:?\s*(\d+)|(\d+)\s*years?\s*old|उम्र\s*:?\s*(\d+)/i,
  );
  if (ageMatch) {
    info.age = parseInt(ageMatch[1] || ageMatch[2] || ageMatch[3]);
  }

  // Extract income
  const incomeMatch = text.match(
    /income\s*:?\s*(\d+)|आय\s*:?\s*(\d+)|salary\s*:?\s*(\d+)/i,
  );
  if (incomeMatch) {
    info.income = parseInt(incomeMatch[1] || incomeMatch[2] || incomeMatch[3]);
  }

  // Extract state
  const states = [
    "maharashtra",
    "punjab",
    "haryana",
    "uttar pradesh",
    "up",
    "bihar",
    "rajasthan",
    "gujarat",
    "madhya pradesh",
    "mp",
  ];
  const stateMatch = states.find((state) => text.toLowerCase().includes(state));
  if (stateMatch) {
    info.state = stateMatch;
  }

  // Extract occupation
  if (
    text.toLowerCase().includes("farmer") ||
    text.toLowerCase().includes("किसान")
  ) {
    info.occupation = "farmer";
  }

  return info;
};

// Match schemes based on user info
export const matchSchemes = (userInfo) => {
  return mockSchemes.filter((scheme) => {
    const { age, income, occupation } = userInfo;
    const { eligibility } = scheme;

    // Check age
    if (age && (age < eligibility.minAge || age > eligibility.maxAge)) {
      return false;
    }

    // Check income
    if (
      income &&
      (income < eligibility.minIncome || income > eligibility.maxIncome)
    ) {
      return false;
    }

    // Check occupation
    if (occupation && eligibility.occupation[0] !== "all") {
      if (!eligibility.occupation.includes(occupation)) {
        return false;
      }
    }

    return true;
  });
};

// Generate response based on user input
export const generateResponse = (userInput, userInfo, language = "en") => {
  const input = userInput.toLowerCase();

  // Check if user is asking about schemes
  if (
    input.includes("scheme") ||
    input.includes("योजना") ||
    input.includes("benefit") ||
    input.includes("लाभ")
  ) {
    const schemes = matchSchemes(userInfo);

    if (schemes.length > 0) {
      if (language === "hi") {
        return `मैंने आपके लिए ${schemes.length} योजनाएं पाईं:\n\n${schemes.map((s, i) => `${i + 1}. ${s.nameHi}\n   ${s.descriptionHi}`).join("\n\n")}`;
      } else {
        return `I found ${schemes.length} schemes for you:\n\n${schemes.map((s, i) => `${i + 1}. ${s.nameEn}\n   ${s.description}`).join("\n\n")}`;
      }
    } else {
      if (language === "hi") {
        return "कृपया अपनी उम्र, राज्य और आय बताएं ताकि मैं आपके लिए सही योजनाएं ढूंढ सकूं।";
      } else {
        return "Please tell me your age, state, and income so I can find the right schemes for you.";
      }
    }
  }

  // Check if user provided information
  if (
    userInfo.age ||
    userInfo.income ||
    userInfo.state ||
    userInfo.occupation
  ) {
    const schemes = matchSchemes(userInfo);

    if (schemes.length > 0) {
      if (language === "hi") {
        return `बढ़िया! आपकी जानकारी के आधार पर, आप ${schemes.length} योजनाओं के लिए पात्र हैं:\n\n${schemes.map((s, i) => `${i + 1}. ${s.nameHi}\n   ${s.descriptionHi}`).join("\n\n")}\n\nक्या आप किसी योजना के बारे में अधिक जानना चाहेंगे?`;
      } else {
        return `Great! Based on your information, you are eligible for ${schemes.length} schemes:\n\n${schemes.map((s, i) => `${i + 1}. ${s.nameEn}\n   ${s.description}`).join("\n\n")}\n\nWould you like to know more about any scheme?`;
      }
    } else {
      if (language === "hi") {
        return "आपकी जानकारी के आधार पर, मुझे कोई मिलान योजना नहीं मिली। कृपया अपनी जानकारी की जांच करें।";
      } else {
        return "Based on your information, I could not find any matching schemes. Please check your information.";
      }
    }
  }

  // Default response
  if (language === "hi") {
    return "नमस्ते! मैं SarkariSaathi हूं। मैं आपको सरकारी योजनाओं के बारे में जानकारी देने में मदद कर सकता हूं। कृपया अपनी उम्र, राज्य और आय बताएं।";
  } else {
    return "Hello! I am SarkariSaathi. I can help you find information about government schemes. Please tell me your age, state, and income.";
  }
};

// Detect language from text
export const detectLanguage = (text) => {
  // Check for Devanagari script (Hindi)
  if (/[\u0900-\u097F]/.test(text)) {
    return "hi";
  }
  return "en";
};

export { mockSchemes };
