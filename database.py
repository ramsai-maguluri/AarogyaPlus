import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'health_hub.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_schema(cursor):
    """Ensure all required columns exist in the users table"""
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    new_cols = {
        'profile_pic': "TEXT DEFAULT 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80'",
        'blood_group': "TEXT DEFAULT 'O+'",
        'emergency_contact': "TEXT DEFAULT ''",
        'address': "TEXT DEFAULT ''",
        'allergies': "TEXT DEFAULT 'None reported'",
        'medical_history': "TEXT DEFAULT 'None'"
    }

    for col_name, col_type in new_cols.items():
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to users table.")

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            gender TEXT DEFAULT 'Male',
            age INTEGER DEFAULT 28,
            role TEXT DEFAULT 'patient',
            profile_pic TEXT DEFAULT 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80',
            blood_group TEXT DEFAULT 'O+',
            emergency_contact TEXT DEFAULT '',
            address TEXT DEFAULT '',
            allergies TEXT DEFAULT 'None reported',
            medical_history TEXT DEFAULT 'None',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    migrate_schema(cursor)

    # Doctors Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            qualification TEXT NOT NULL,
            experience_years INTEGER NOT NULL,
            hospital TEXT NOT NULL,
            location TEXT NOT NULL,
            consultation_fee REAL NOT NULL,
            rating REAL NOT NULL,
            reviews_count INTEGER NOT NULL,
            available_days TEXT NOT NULL,
            available_time_slots TEXT NOT NULL,
            image_url TEXT,
            bio TEXT,
            languages TEXT
        )
    ''')

    # Medicines Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand_name TEXT NOT NULL,
            generic_name TEXT NOT NULL,
            category TEXT NOT NULL,
            dosage_form TEXT NOT NULL,
            strength TEXT NOT NULL,
            uses_summary TEXT NOT NULL,
            uses_detailed TEXT NOT NULL,
            how_it_works TEXT NOT NULL,
            dosage_instructions TEXT NOT NULL,
            side_effects TEXT NOT NULL,
            precautions TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            price REAL NOT NULL,
            prescription_required INTEGER DEFAULT 0,
            tags TEXT
        )
    ''')

    # Appointments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_number TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            patient_name TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            patient_age INTEGER NOT NULL,
            patient_gender TEXT NOT NULL,
            doctor_id INTEGER NOT NULL,
            doctor_name TEXT NOT NULL,
            doctor_specialty TEXT NOT NULL,
            hospital_name TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            problem_description TEXT,
            status TEXT DEFAULT 'Confirmed',
            fee REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()

    # Re-seed doctors with 18+ comprehensive specialists
    cursor.execute('SELECT COUNT(*) FROM doctors')
    doc_count = cursor.fetchone()[0]
    if doc_count < 15:
        cursor.execute('DELETE FROM doctors')
        seed_doctors(cursor)

    # Re-seed medicines with comprehensive English catalog
    cursor.execute('SELECT COUNT(*) FROM medicines')
    med_count = cursor.fetchone()[0]
    if med_count < 20:
        cursor.execute('DELETE FROM medicines')
        seed_medicines(cursor)

    # Seed demo users if missing
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        seed_users(cursor)

    conn.commit()
    conn.close()
    print("Database initialized and verified successfully!")

def seed_users(cursor):
    demo_users = [
        (
            'Kalyan Kumar',
            'patient@example.com',
            generate_password_hash('password123'),
            '9876543210',
            'Male',
            28,
            'patient',
            'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80',
            'O+',
            '9876543211 (Brother)',
            'Madhapur, Hyderabad, Telangana',
            'Penicillin (Mild Rash)',
            'Seasonal allergic rhinitis'
        ),
        (
            'Dr. Sneha Reddy',
            'doctor@example.com',
            generate_password_hash('doctor123'),
            '9123456780',
            'Female',
            38,
            'doctor',
            'https://images.unsplash.com/photo-1594824813501-483525287f39?w=150&auto=format&fit=crop&q=80',
            'B+',
            '9123456781',
            'Banjara Hills, Hyderabad',
            'None',
            'None'
        )
    ]
    cursor.executemany('''
        INSERT INTO users (name, email, password_hash, phone, gender, age, role, profile_pic, blood_group, emergency_contact, address, allergies, medical_history)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', demo_users)

def seed_doctors(cursor):
    doctors_data = [
        (
            "Dr. Rajesh Varma",
            "General Physician",
            "MBBS, MD (Internal Medicine)",
            14,
            "Apollo Health City, Jubilee Hills",
            "Hyderabad",
            500.0,
            4.9,
            340,
            "Mon, Tue, Wed, Thu, Fri, Sat",
            json.dumps(["09:00 AM", "10:00 AM", "11:30 AM", "02:00 PM", "04:30 PM", "06:00 PM"]),
            "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80",
            "Senior General Physician specializing in infectious diseases, viral fevers, diabetes management, hypertension, and routine health checks.",
            "English, Telugu, Hindi"
        ),
        (
            "Dr. Sneha Reddy",
            "Cardiologist",
            "MBBS, MD, DM (Cardiology), FACC",
            12,
            "Care Hospitals, Banjara Hills",
            "Hyderabad",
            850.0,
            4.95,
            412,
            "Mon, Wed, Fri, Sat",
            json.dumps(["10:00 AM", "11:00 AM", "12:30 PM", "03:00 PM", "05:00 PM"]),
            "https://images.unsplash.com/photo-1594824813501-483525287f39?w=400&auto=format&fit=crop&q=80",
            "Leading interventional cardiologist experienced in coronary artery disease, heart failure, ECG/ECHO assessment, and hypertension management.",
            "English, Telugu"
        ),
        (
            "Dr. Ananya Sharma",
            "Dermatologist & Cosmetologist",
            "MBBS, DVD, MD (Dermatology)",
            9,
            "KIMS Hospital, Secunderabad",
            "Hyderabad",
            600.0,
            4.85,
            280,
            "Tue, Thu, Sat, Sun",
            json.dumps(["11:00 AM", "12:00 PM", "02:30 PM", "04:00 PM", "06:30 PM"]),
            "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&auto=format&fit=crop&q=80",
            "Consultant dermatologist specializing in eczema, psoriasis, acne therapy, hair fall treatments, laser procedures, and skin allergy diagnostics.",
            "English, Hindi, Telugu"
        ),
        (
            "Dr. P. Venkatesh",
            "Neurologist",
            "MBBS, MD, DM (Neurology)",
            16,
            "Yashoda Hospitals, Somajiguda",
            "Hyderabad",
            900.0,
            4.9,
            395,
            "Mon, Tue, Thu, Fri",
            json.dumps(["09:30 AM", "11:00 AM", "01:00 PM", "03:30 PM", "05:30 PM"]),
            "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80",
            "Senior Neurologist treating chronic migraines, epilepsy, stroke rehabilitation, peripheral neuropathy, sciatica, and movement disorders.",
            "English, Telugu"
        ),
        (
            "Dr. Madhavi Latha",
            "Pediatrician (Child Specialist)",
            "MBBS, DCH, DNB (Pediatrics)",
            11,
            "Rainbow Children's Hospital, Kondapur",
            "Hyderabad",
            600.0,
            4.92,
            510,
            "Mon, Tue, Wed, Thu, Fri, Sat",
            json.dumps(["09:00 AM", "10:30 AM", "12:00 PM", "04:00 PM", "05:30 PM", "07:00 PM"]),
            "https://images.unsplash.com/photo-1614608682850-e0d6ed316d47?w=400&auto=format&fit=crop&q=80",
            "Compassionate pediatrician handling newborn care, childhood immunizations, seasonal respiratory infections, and developmental milestones.",
            "English, Telugu, Hindi"
        ),
        (
            "Dr. Vikram Naidu",
            "Orthopedic Surgeon",
            "MBBS, MS (Orthopedics), M.Ch (Joint Replacement)",
            15,
            "Continental Hospitals, Gachibowli",
            "Hyderabad",
            750.0,
            4.88,
            320,
            "Mon, Wed, Thu, Sat",
            json.dumps(["10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "06:00 PM"]),
            "https://images.unsplash.com/photo-1622902046580-2b47f47f5471?w=400&auto=format&fit=crop&q=80",
            "Specialist in knee & hip replacements, arthroscopy, sports injuries, ligament reconstruction, and osteoarthritic spine management.",
            "English, Telugu"
        ),
        (
            "Dr. K. Sravani",
            "Gynecologist & Obstetrician",
            "MBBS, MS (OBG), FMAS",
            10,
            "Fernandez Hospital, Hyderguda",
            "Hyderabad",
            650.0,
            4.94,
            445,
            "Mon, Tue, Wed, Thu, Fri",
            json.dumps(["10:00 AM", "11:30 AM", "01:00 PM", "03:00 PM", "05:00 PM"]),
            "https://images.unsplash.com/photo-1651008376811-b90baee60c1f?w=400&auto=format&fit=crop&q=80",
            "Expert in high-risk pregnancy care, PCOS/PCOD management, menstrual irregularities, fertility counseling, and minimally invasive gynecological surgery.",
            "English, Telugu"
        ),
        (
            "Dr. Harish Rao",
            "ENT Specialist",
            "MBBS, MS (ENT / Otorhinolaryngology)",
            13,
            "MaxCure Hospitals, Madhapur",
            "Hyderabad",
            550.0,
            4.82,
            260,
            "Tue, Wed, Fri, Sat",
            json.dumps(["09:30 AM", "11:00 AM", "12:30 PM", "04:30 PM", "06:00 PM"]),
            "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=400&auto=format&fit=crop&q=80",
            "Expert in ear infections, sinusitis, endoscopic sinus surgery, tonsillitis, hearing loss, vertigo, and allergic rhinitis.",
            "English, Telugu, Hindi"
        ),
        (
            "Dr. Gayatri Devi",
            "Ophthalmologist (Eye Specialist)",
            "MBBS, MS (Ophthalmology), FICO",
            14,
            "L.V. Prasad Eye Institute, Banjara Hills",
            "Hyderabad",
            600.0,
            4.96,
            480,
            "Mon, Tue, Wed, Thu, Fri, Sat",
            json.dumps(["09:00 AM", "10:30 AM", "12:00 PM", "02:30 PM", "04:00 PM"]),
            "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=400&auto=format&fit=crop&q=80",
            "Renowned eye specialist offering comprehensive vision checks, cataract advice, refractive LASIK counseling, and glaucoma management.",
            "English, Telugu"
        ),
        (
            "Dr. Srinivas Goud",
            "Gastroenterologist",
            "MBBS, MD, DM (Gastroenterology)",
            17,
            "AIG Hospitals, Gachibowli",
            "Hyderabad",
            950.0,
            4.93,
            380,
            "Mon, Wed, Thu, Fri",
            json.dumps(["10:00 AM", "11:30 AM", "02:00 PM", "04:00 PM", "05:30 PM"]),
            "https://images.unsplash.com/photo-1536064479547-7ee40b74b807?w=400&auto=format&fit=crop&q=80",
            "Specialist in peptic ulcers, acid reflux (GERD), fatty liver, IBS, inflammatory bowel disease, endoscopy, and digestive disorders.",
            "English, Telugu, Hindi"
        ),
        (
            "Dr. Kavitha Menon",
            "Psychiatrist & Mental Wellness",
            "MBBS, MD (Psychiatry)",
            8,
            "Asha Hospital, Banjara Hills",
            "Hyderabad",
            700.0,
            4.89,
            210,
            "Tue, Thu, Fri, Sat",
            json.dumps(["11:00 AM", "01:00 PM", "03:30 PM", "05:00 PM", "06:30 PM"]),
            "https://images.unsplash.com/photo-1527613426441-4da17471b66d?w=400&auto=format&fit=crop&q=80",
            "Compassionate counseling and clinical treatment for anxiety, clinical depression, work stress, sleep disorders, and panic syndromes.",
            "English, Hindi, Telugu"
        ),
        (
            "Dr. Arun Kumar",
            "Pulmonologist (Chest & Lungs)",
            "MBBS, DTCD, DNB (Pulmonary Medicine)",
            12,
            "Sunshine Hospitals, Secunderabad",
            "Hyderabad",
            650.0,
            4.87,
            295,
            "Mon, Tue, Wed, Fri, Sat",
            json.dumps(["10:00 AM", "11:30 AM", "01:30 PM", "04:00 PM", "06:00 PM"]),
            "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&auto=format&fit=crop&q=80",
            "Expert in bronchial asthma, COPD, chronic bronchitis, interstitial lung diseases, post-COVID lung recovery, and sleep apnea.",
            "English, Telugu"
        ),
        (
            "Dr. Siddharth Verma",
            "Medical Oncologist (Cancer Specialist)",
            "MBBS, MD, DM (Medical Oncology)",
            16,
            "American Oncology Institute, Nanakramguda",
            "Hyderabad",
            1000.0,
            4.97,
            330,
            "Mon, Tue, Wed, Fri",
            json.dumps(["10:00 AM", "11:30 AM", "02:00 PM", "04:30 PM"]),
            "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?w=400&auto=format&fit=crop&q=80",
            "Experienced medical oncologist providing targeted cancer therapies, chemotherapy protocols, immunotherapy, and genetic cancer screening.",
            "English, Hindi, Telugu"
        ),
        (
            "Dr. Pooja Chawla",
            "Nephrologist (Kidney Specialist)",
            "MBBS, MD, DM (Nephrology)",
            13,
            "Asian Institute of Nephrology and Urology (AINU)",
            "Hyderabad",
            850.0,
            4.91,
            275,
            "Mon, Wed, Thu, Sat",
            json.dumps(["09:30 AM", "11:00 AM", "01:30 PM", "03:30 PM", "05:00 PM"]),
            "https://images.unsplash.com/photo-1594824813689-b8833e21855b?w=400&auto=format&fit=crop&q=80",
            "Specialist in chronic kidney disease (CKD), acute kidney injury, dialysis care, kidney transplant evaluation, and electrolyte imbalances.",
            "English, Hindi, Telugu"
        ),
        (
            "Dr. Manoj Deshmukh",
            "Endocrinologist (Diabetes & Thyroid)",
            "MBBS, MD, DM (Endocrinology)",
            15,
            "Apollo Sugar Clinics, Jubilee Hills",
            "Hyderabad",
            800.0,
            4.89,
            360,
            "Tue, Wed, Fri, Sat",
            json.dumps(["10:00 AM", "11:30 AM", "01:00 PM", "04:00 PM", "06:00 PM"]),
            "https://images.unsplash.com/photo-1622253694238-3b22139576c6?w=400&auto=format&fit=crop&q=80",
            "Specialist in refractory diabetes mellitus, thyroid disorders (hypothyroidism, Hashimoto's), osteoporosis, hormonal imbalances, and pituitary disorders.",
            "English, Marathi, Telugu, Hindi"
        ),
        (
            "Dr. Tarun Khanna",
            "Urologist & Andrologist",
            "MBBS, MS (General Surgery), M.Ch (Urology)",
            14,
            "Medicover Hospitals, Hitec City",
            "Hyderabad",
            750.0,
            4.88,
            310,
            "Mon, Tue, Thu, Sat",
            json.dumps(["10:30 AM", "12:00 PM", "02:30 PM", "04:30 PM", "06:00 PM"]),
            "https://images.unsplash.com/photo-1622902046580-2b47f47f5471?w=400&auto=format&fit=crop&q=80",
            "Expert in kidney stones, laser lithotripsy, enlarged prostate (BPH), urinary tract infections, and male reproductive health.",
            "English, Hindi, Punjabi, Telugu"
        ),
        (
            "Dr. Meera Nambiar",
            "Rheumatologist (Arthritis & Autoimmune)",
            "MBBS, MD, DNB (Rheumatology)",
            11,
            "CARE Outpatient Centre, Banjara Hills",
            "Hyderabad",
            800.0,
            4.93,
            245,
            "Mon, Wed, Fri",
            json.dumps(["10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM"]),
            "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&auto=format&fit=crop&q=80",
            "Specialized in rheumatoid arthritis, lupus (SLE), ankylosing spondylitis, gout, vasculitis, and chronic joint inflammation.",
            "English, Malayalam, Telugu, Hindi"
        ),
        (
            "Dr. Rohit Singhania",
            "Plastic & Reconstructive Surgeon",
            "MBBS, MS, M.Ch (Plastic Surgery)",
            15,
            "Continental Hospitals, Gachibowli",
            "Hyderabad",
            900.0,
            4.86,
            195,
            "Tue, Thu, Sat",
            json.dumps(["11:00 AM", "01:00 PM", "03:30 PM", "05:30 PM"]),
            "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80",
            "Specialist in reconstructive microsurgery, trauma reconstruction, burn management, scar revision, and aesthetic surgical procedures.",
            "English, Hindi, Telugu"
        )
    ]

    cursor.executemany('''
        INSERT INTO doctors (
            name, specialty, qualification, experience_years, hospital, location,
            consultation_fee, rating, reviews_count, available_days,
            available_time_slots, image_url, bio, languages
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', doctors_data)

def seed_medicines(cursor):
    medicines_data = [
        (
            "Dolo 650 Tablet",
            "Dolo 650",
            "Paracetamol / Acetaminophen (650mg)",
            "Fever & Pain Relief",
            "Tablet",
            "650 mg",
            "Used to treat high fever, headaches, body aches, toothache, and mild joint pains.",
            "Dolo 650 contains Paracetamol (650mg). It acts as an antipyretic (reduces fever) and analgesic (relieves mild to moderate pain). It is widely recommended during viral fevers, seasonal flus, toothaches, earaches, and backache.",
            "Inhibits prostaglandin synthesis in the central nervous system, altering temperature regulation in the hypothalamic center and raising the body's pain threshold.",
            "Take 1 tablet after meals with plenty of water. Maintain a minimum interval of 4 to 6 hours between doses. Do not exceed 4 tablets (2600mg) in 24 hours without medical supervision.",
            "Nausea, mild stomach discomfort. Excessive or prolonged usage can cause severe hepatic (liver) toxicity.",
            "Avoid alcohol while taking paracetamol. Do not combine with other OTC medicines containing paracetamol to prevent accidental overdose. Liver and kidney patients must consult a doctor first.",
            "Micro Labs Ltd",
            32.50,
            0,
            "fever, headache, body pain, cold, dolo, paracetamol, viral, temperature, painkiller"
        ),
        (
            "Augmentin 625 Duo Tablet",
            "Augmentin 625",
            "Amoxicillin (500mg) + Clavulanic Acid (125mg)",
            "Antibiotic",
            "Tablet",
            "625 mg",
            "Broad-spectrum antibiotic used to treat bacterial infections of the lungs, throat, ear, urinary tract, skin, and dental abscesses.",
            "Augmentin 625 Duo is a powerful penicillin-type antibiotic. Amoxicillin halts bacterial cell wall synthesis, while Clavulanic acid inhibits beta-lactamase enzymes produced by resistant bacteria, ensuring broad-spectrum bactericidal activity.",
            "Amoxicillin prevents bacterial cell wall formation. Clavulanic acid blocks beta-lactamase enzymes produced by resistant bacteria, preventing degradation of amoxicillin.",
            "Take 1 tablet twice daily (morning and night) at the beginning of a meal to reduce gastrointestinal intolerance. Complete the full prescribed course (typically 5 to 7 days).",
            "Diarrhea, nausea, vomiting, mild skin rash, oral or vaginal fungal thrush.",
            "Always complete the full course to prevent bacterial resistance. Do not use for viral infections (colds, flu). Inform your physician if you have a known penicillin allergy.",
            "GlaxoSmithKline Pharmaceuticals Ltd (GSK)",
            205.00,
            1,
            "antibiotic, throat infection, cough, ear infection, tooth infection, augmentin, bacterial"
        ),
        (
            "Pantocid 40 Tablet",
            "Pantocid 40",
            "Pantoprazole (40mg)",
            "Acidity & Heartburn",
            "Tablet",
            "40 mg",
            "Treats gastroesophageal reflux disease (GERD), acid reflux, gastric ulcers, heartburn, and excessive stomach acid production.",
            "Pantocid 40 is a Proton Pump Inhibitor (PPI). It reduces the amount of acid produced in the stomach, providing long-lasting relief from acid indigestion and helping heal damage to the esophageal lining.",
            "Covalently binds to the H+/K+ ATPase enzyme system (proton pump) of gastric parietal cells, thereby inhibiting basal and stimulated gastric acid secretion.",
            "Take 1 tablet once daily in the morning, 30 to 60 minutes before breakfast. Swallow whole with water; do not crush or chew.",
            "Headache, mild diarrhea, abdominal flatulence, dizziness, mild nausea.",
            "Long-term use can diminish calcium and vitamin B12 absorption. If taken for prolonged periods, regular physician review is advised.",
            "Sun Pharmaceutical Industries Ltd",
            145.00,
            0,
            "acidity, gas, heartburn, stomach pain, gerd, ulcer, digestion, pantoprazole"
        ),
        (
            "Cetirizine 10mg (Cetzine)",
            "Cetzine 10",
            "Cetirizine Dihydrochloride (10mg)",
            "Allergy & Cold",
            "Tablet",
            "10 mg",
            "Provides fast relief from allergy symptoms including runny nose, sneezing, itchy throat, watery eyes, and urticaria (skin hives).",
            "Cetirizine is a non-sedating, second-generation antihistamine that selectively blocks peripheral H1 histamine receptors, suppressing histamine-mediated allergic symptoms and nasal congestion.",
            "Selectively antagonizes peripheral H1 histamine receptors, preventing allergic capillary permeability and tissue edema.",
            "Take 1 tablet once daily, preferably at bedtime with or without food. May cause mild drowsiness in sensitive individuals.",
            "Drowsiness, dry mouth, tiredness, mild headache.",
            "May cause drowsiness; avoid driving or operating heavy machinery until your reaction is known. Avoid consuming alcohol concurrently.",
            "Dr. Reddy's Laboratories",
            21.00,
            0,
            "allergy, sneezing, runny nose, cold, skin rash, itching, hives, cetirizine"
        ),
        (
            "Azithral 500 Tablet",
            "Azithral 500",
            "Azithromycin (500mg)",
            "Antibiotic",
            "Tablet",
            "500 mg",
            "Used to treat bacterial infections of the respiratory tract (bronchitis, pneumonia), tonsillitis, sinus infections, and skin infections.",
            "Azithral 500 is an azalide antibiotic that reversibly binds to the 50S ribosomal subunit of susceptible microorganisms, inhibiting protein synthesis and halting bacterial proliferation.",
            "Inhibits transpeptidation and protein synthesis by binding to the 50S ribosomal subunit in susceptible bacteria.",
            "Take 1 tablet once daily at the same time, either 1 hour before or 2 hours after meals with water. Usually prescribed for 3 to 5 days.",
            "Nausea, vomiting, diarrhea, abdominal cramps, temporary taste alteration.",
            "Do not consume antacids containing aluminum or magnesium simultaneously. Complete the entire course strictly as prescribed.",
            "Alembic Pharmaceuticals Ltd",
            132.00,
            1,
            "antibiotic, sore throat, tonsils, dry cough, sinus, azithral, azithromycin"
        ),
        (
            "Glycomet-GP 1 Forte Tablet",
            "Glycomet-GP 1",
            "Metformin (1000mg) + Glimepiride (1mg)",
            "Diabetes Management",
            "Tablet",
            "Extended Release",
            "Used to regulate elevated blood glucose levels in patients with type 2 diabetes mellitus alongside diet and physical exercise.",
            "Dual-action formula: Glimepiride stimulates beta cells in the pancreas to release insulin, while Metformin reduces hepatic glucose production and enhances peripheral insulin sensitivity in skeletal muscle.",
            "Glimepiride closes ATP-sensitive potassium channels in pancreatic beta cells; Metformin activates AMP-activated protein kinase (AMPK) to decrease gluconeogenesis.",
            "Take 1 tablet once daily with or immediately after the first main meal (breakfast) with water.",
            "Hypoglycemia (low blood sugar), gastrointestinal upset, metallic taste, nausea.",
            "Regularly monitor blood glucose. Always keep fast-acting glucose tablets or fruit juice handy in case of hypoglycemic symptoms.",
            "USV Ltd",
            110.00,
            1,
            "diabetes, sugar, blood sugar, glucose, metformin, glimepiride, glycomet"
        ),
        (
            "Telma 40 Tablet",
            "Telma 40",
            "Telmisartan (40mg)",
            "Hypertension & BP",
            "Tablet",
            "40 mg",
            "Used to lower elevated blood pressure (hypertension) and reduce cardiovascular morbidity and mortality in high-risk patients.",
            "Telmisartan is an Angiotensin Receptor Blocker (ARB). It relaxes blood vessels by blocking the action of angiotensin II, facilitating smooth blood flow and reducing cardiac workload.",
            "Selectively blocks angiotensin II type 1 (AT1) receptors, producing vasodilation and decreasing aldosterone secretion.",
            "Take 1 tablet once daily with or without food at the same time each day (typically in the morning).",
            "Dizziness, back pain, sinus congestion, postural hypotension.",
            "Do not discontinue without consulting your physician. Avoid potassium supplements unless specifically recommended. Contraindicated during pregnancy.",
            "Glenmark Pharmaceuticals Ltd",
            128.00,
            1,
            "blood pressure, bp, hypertension, heart, stroke prevention, telmisartan, telma"
        ),
        (
            "Combiflam Tablet",
            "Combiflam",
            "Ibuprofen (400mg) + Paracetamol (325mg)",
            "Pain & Inflammation",
            "Tablet",
            "725 mg",
            "Indicated for acute musculoskeletal pain, joint inflammation, dental extraction pain, dysmenorrhea, and post-operative discomfort.",
            "Combiflam combines Ibuprofen (an NSAID that reduces swelling and inflammation by inhibiting cyclooxygenase) with Paracetamol (which raises the pain threshold).",
            "Inhibits COX-1 and COX-2 enzymes to decrease inflammatory prostaglandin synthesis, while providing central antipyretic/analgesic action.",
            "Take 1 tablet after meals with a full glass of water. Never take on an empty stomach to prevent gastric mucosal irritation.",
            "Heartburn, indigestion, nausea, mild epigastric discomfort.",
            "Patients with peptic ulcers, renal impairment, or severe asthma should consult their doctor before using. Do not exceed recommended dosage.",
            "Sanofi India Ltd",
            48.50,
            0,
            "pain, swelling, joint pain, arthritis, toothache, muscle ache, ibuprofen, combiflam"
        ),
        (
            "Montair-LC Tablet",
            "Montair-LC",
            "Montelukast (10mg) + Levocetirizine (5mg)",
            "Asthma & Respiratory Allergy",
            "Tablet",
            "15 mg",
            "Used for chronic allergic rhinitis, seasonal asthma prophylaxis, nocturnal coughing, wheezing, and allergic bronchospasm.",
            "Levocetirizine antagonizes histamine H1 receptors, while Montelukast blocks cysteinyl leukotriene receptors, suppressing both early and late phase allergic airway inflammation.",
            "Dual action: competitive H1 receptor blockade plus cysteinyl leukotriene receptor-1 (CysLT1) antagonism.",
            "Take 1 tablet once daily in the evening or before bedtime with water, with or without food.",
            "Mild drowsiness, dry mouth, headache, fatigue, occasional vivid dreams.",
            "May cause mild drowsiness. Avoid alcohol and sedatives. Not intended for immediate relief of acute asthma attacks.",
            "Cipla Ltd",
            195.00,
            1,
            "asthma, allergy, wheezing, breathing problem, cough, montelukast, levocetirizine"
        ),
        (
            "Atorva 10 Tablet",
            "Atorva 10",
            "Atorvastatin (10mg)",
            "Cholesterol & Lipid Control",
            "Tablet",
            "10 mg",
            "Prescribed to reduce low-density lipoprotein (LDL) cholesterol and triglycerides while raising HDL, preventing atherosclerotic cardiovascular disease.",
            "Atorvastatin is an HMG-CoA reductase inhibitor (statin). It decreases hepatic cholesterol synthesis and upregulates cell-surface LDL receptors, clearing LDL from systemic circulation.",
            "Competitively inhibits 3-hydroxy-3-methylglutaryl-coenzyme A (HMG-CoA) reductase, the rate-limiting enzyme in cholesterol biosynthesis.",
            "Take 1 tablet once daily, preferably in the evening or at bedtime, with or without food.",
            "Myalgia (muscle ache), joint stiffness, mild indigestion, headache.",
            "Promptly report unexplained muscle pain or weakness to your doctor. Avoid grapefruit juice while on atorvastatin. Strictly contraindicated during pregnancy.",
            "Zydus Cadila",
            98.00,
            1,
            "cholesterol, ldl, heart attack, lipid, triglycerides, atorvastatin, atorva"
        ),
        (
            "Lipitor 20mg Tablet",
            "Lipitor",
            "Atorvastatin Calcium (20mg)",
            "Cardiovascular & Cholesterol",
            "Tablet",
            "20 mg",
            "Globally recognized statin indicated for hypercholesterolemia, prevention of heart attack, stroke, and revascularization procedures.",
            "Lipitor lowers bad cholesterol (LDL) and triglycerides and raises good cholesterol (HDL) by inhibiting HMG-CoA reductase in the liver.",
            "Reversible competitive inhibitor of the microsomal enzyme HMG-CoA reductase, increasing hepatic LDL uptake.",
            "Take 1 tablet orally once daily with or without food at the same time each day.",
            "Nasopharyngitis, arthralgia, diarrhea, dyspepsia, muscle discomfort.",
            "Liver function monitoring recommended. Do not take during pregnancy or breastfeeding.",
            "Pfizer Inc.",
            340.00,
            1,
            "cholesterol, lipitor, atorvastatin, heart, cardiac, statin, global"
        ),
        (
            "Ozempic 0.5mg / 1mg Injection",
            "Ozempic",
            "Semaglutide (2mg/3ml pre-filled pen)",
            "Diabetes & Weight Management",
            "Subcutaneous Injection",
            "0.5 mg / dose",
            "Indicated as an adjunct to diet and exercise to improve glycemic control in adults with type 2 diabetes mellitus and reduce major cardiovascular events.",
            "Ozempic is a GLP-1 receptor agonist. It stimulates glucose-dependent insulin secretion, suppresses glucagon, and delays gastric emptying, promoting satiety and blood sugar regulation.",
            "Binds selectively to and activates the glucagon-like peptide-1 (GLP-1) receptor.",
            "Administered once weekly subcutaneously into the abdomen, thigh, or upper arm on the same day each week, any time of day, with or without food.",
            "Nausea, vomiting, diarrhea, abdominal pain, constipation.",
            "Contraindicated in patients with personal or family history of medullary thyroid carcinoma (MTC) or MEN 2.",
            "Novo Nordisk",
            7500.00,
            1,
            "ozempic, semaglutide, diabetes, glp1, weight loss, blood sugar, injection"
        ),
        (
            "Nexium 40mg Tablet",
            "Nexium",
            "Esomeprazole Magnesium (40mg)",
            "Gastrointestinal & Ulcers",
            "Tablet",
            "40 mg",
            "Prescribed for healing erosive esophagitis, gastroesophageal reflux disease (GERD), and Zollinger-Ellison syndrome.",
            "Nexium is the S-isomer of omeprazole. It provides potent and sustained suppression of gastric acid by targeting the proton pump in gastric parietal cells.",
            "Specifically inhibits the H+/K+-ATPase enzyme at the secretory surface of the gastric parietal cell.",
            "Take 1 tablet once daily, at least 1 hour before a meal, swallowed whole with water.",
            "Headache, diarrhea, nausea, flatulence, abdominal pain, constipation.",
            "Prolonged usage may increase risk of hypomagnesemia and bone fractures. Follow physician dosage instructions.",
            "AstraZeneca",
            210.00,
            1,
            "nexium, esomeprazole, acidity, gerd, heartburn, stomach, global"
        ),
        (
            "Gelusil MPS Liquid / Antacid",
            "Gelusil MPS",
            "Aluminium Hydroxide + Magnesium Hydroxide + Simethicone",
            "Antacid & Antiflatulent",
            "Liquid Suspension",
            "200 ml",
            "Provides instant soothing relief from hyperacidity, acid indigestion, heartburn, gas distress, and stomach fullness.",
            "Neutralizes gastric hydrochloric acid rapidly and breaks surface tension of gastrointestinal gas bubbles, permitting easy gas evacuation.",
            "Chemical neutralization of gastric acid coupled with surfactant simethicone action.",
            "Take 10ml to 20ml (2 to 4 teaspoons) 30 to 60 minutes after meals and at bedtime, or when symptoms arise. Shake bottle well.",
            "Mild bowel changes (occasional loose stools or constipation).",
            "Do not administer concurrently with tetracyclines or fluoroquinolones within 2 hours as absorption may be impaired.",
            "Pfizer Ltd",
            125.00,
            0,
            "gas, acidity, heartburn, bloating, indigestion, gelusil, antacid, stomach burning"
        ),
        (
            "Omez 20 Capsule",
            "Omez 20",
            "Omeprazole (20mg)",
            "Gastric Ulcer & Reflux",
            "Capsule",
            "20 mg",
            "Used to treat and heal peptic ulcer disease, gastric ulcers, reflux esophagitis, and eradicate H. pylori alongside antibiotics.",
            "Suppresses gastric acid secretion for up to 24 hours by irreversibly blocking the gastric proton pump.",
            "Inhibits H+/K+-ATPase at the secretory surface of gastric parietal cells.",
            "Take 1 capsule once daily in the morning, 30 minutes before breakfast. Swallow whole; do not open capsule or crush granules.",
            "Mild headache, diarrhea, nausea, abdominal discomfort.",
            "Long-term use should be evaluated by a healthcare professional.",
            "Dr. Reddy's Laboratories",
            58.00,
            0,
            "ulcer, acidity, gas, omez, omeprazole, burning sensation, stomach"
        ),
        (
            "Ascoril D Plus Syrup",
            "Ascoril D Plus",
            "Dextromethorphan + Phenylephrine + Chlorpheniramine",
            "Dry Cough & Cold",
            "Syrup",
            "100 ml",
            "Relieves non-productive dry cough, throat tickling, nasal congestion, runny nose, and allergic sneezing fits.",
            "Dextromethorphan acts centrally on the cough center in the medulla; Chlorpheniramine blocks H1 histamine receptors; Phenylephrine constricts swollen nasal mucosa.",
            "Central antitussive, competitive H1-antihistamine, and alpha-1 adrenergic vasoconstrictor.",
            "Adults: 5ml to 10ml two to three times daily using the calibrated measuring cup provided.",
            "Mild drowsiness, dry mouth, dizziness, slight sleepiness.",
            "Avoid operating motor vehicles if feeling drowsy. Not intended for productive cough with copious green phlegm.",
            "Glenmark Pharmaceuticals Ltd",
            135.00,
            0,
            "dry cough, throat irritation, cold, cough syrup, ascoril, sneezing"
        ),
        (
            "Shelcal 500 Tablet",
            "Shelcal 500",
            "Calcium (500mg) + Vitamin D3 (250 IU)",
            "Bone & Mineral Supplement",
            "Tablet",
            "500 mg",
            "Treats calcium deficiency, osteopenia, osteoporosis, weak bone density, and supports calcium requirements during pregnancy and lactation.",
            "Supplies elemental calcium derived from natural sources, combined with Vitamin D3 (Cholecalciferol) which facilitates optimal intestinal calcium absorption.",
            "Enhances osteoblastic bone matrix mineralization and suppresses excessive parathyroid hormone secretion.",
            "Take 1 tablet daily after lunch or dinner with a full glass of water. Avoid taking on an empty stomach.",
            "Mild constipation, flatulence, nausea.",
            "Maintain adequate daily fluid intake. Patients with a history of renal calculi (kidney stones) should consult a doctor first.",
            "Torrent Pharmaceuticals Ltd",
            120.00,
            0,
            "calcium, bones, joints, vitamin d3, shelcal, weakness, osteoporosis"
        ),
        (
            "Neurobion Forte Tablet",
            "Neurobion Forte",
            "Vitamin B-Complex (B1, B2, B3, B5, B6, B12)",
            "Neuropathy & Vitamin B Support",
            "Tablet",
            "Standard Formula",
            "Indicated for peripheral neuropathy, nerve tingling, numbness in fingers/feet, mouth ulcers, chronic fatigue, and neuralgia.",
            "Provides neurotropic B-vitamins essential for maintaining nerve myelin sheaths, red blood cell synthesis, and cellular cellular energy metabolism.",
            "Replenishes coenzymes vital for neurotransmitter synthesis and peripheral axonal regeneration.",
            "Take 1 tablet daily with or after food with water.",
            "Bright yellow coloration of urine (completely harmless excretion of excess riboflavin).",
            "Safe for long-term daily dietary supplementation.",
            "Procter & Gamble (P&G)",
            38.00,
            0,
            "nerves, tingling, numbness, mouth ulcer, weakness, vitamin b, b12, neurobion"
        ),
        (
            "Ciproglen 500 / Ciprobid",
            "Ciprobid 500",
            "Ciprofloxacin (500mg)",
            "Antibiotic",
            "Tablet",
            "500 mg",
            "Prescribed for severe urinary tract infections (UTIs), bacterial gastroenteritis, infectious diarrhea, typhoid fever, and bone infections.",
            "Fluoroquinolone antibiotic that stops bacterial DNA synthesis by inhibiting topoisomerase II (DNA gyrase) and topoisomerase IV.",
            "Rapidly bactericidal via selective inhibition of bacterial enzymes required for chromosome replication.",
            "Take 1 tablet every 12 hours (twice daily) for 5 to 7 days as directed. Drink plenty of water throughout the day.",
            "Nausea, mild diarrhea, dizziness, tendon tenderness (rare).",
            "Avoid dairy products (milk, yogurt) and antacids 2 hours before and after administration. Stay well-hydrated.",
            "Zydus Cadila",
            46.00,
            1,
            "antibiotic, uti, urine infection, diarrhea, loose motions, cipro, ciprofloxacin"
        ),
        (
            "Volini Pain Relief Gel",
            "Volini Gel",
            "Diclofenac Diethylamine + Methyl Salicylate + Menthol + Linseed Oil",
            "Topical Analgesic Gel",
            "Gel / Ointment",
            "50 gm",
            "Provides fast penetrating relief for acute back pain, joint stiffness, neck strain, muscle spasms, and sports sprains.",
            "Diclofenac penetrates locally to inhibit inflammatory prostaglandin synthesis, while Menthol and Methyl salicylate create counter-irritant soothing sensations.",
            "Topical micro-emulsion delivery of non-steroidal anti-inflammatory agents to inflamed musculoskeletal tissue.",
            "Apply a thin film over the affected area 3 to 4 times daily and massage gently until absorbed. Wash hands after application.",
            "Mild local tingling, cutaneous warmth, or transient erythema.",
            "For external use only. Do not apply on open abrasions, cuts, mucous membranes, or near the eyes.",
            "Sun Pharmaceutical Industries Ltd",
            145.00,
            0,
            "pain gel, volini, back pain, joint pain, muscle pain, neck pain, sprain, ointment"
        )
    ]

    cursor.executemany('''
        INSERT INTO medicines (
            name, brand_name, generic_name, category, dosage_form, strength,
            uses_summary, uses_detailed, how_it_works,
            dosage_instructions, side_effects, precautions, manufacturer,
            price, prescription_required, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', medicines_data)

if __name__ == '__main__':
    init_db()
