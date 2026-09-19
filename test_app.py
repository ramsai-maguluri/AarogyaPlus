import unittest
import json
import datetime
from app import app
from database import init_db

class TestAarogyaPlusUpgraded(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AarogyaPlus', response.data)
        self.assertIn(b'doctorSearchInput', response.data)
        self.assertIn(b'medicineSearchInput', response.data)
        self.assertIn(b'profileModal', response.data)
        self.assertIn(b'aiChatLauncher', response.data)
        self.assertIn(b'aiChatContainer', response.data)
        self.assertIn(b'themeToggleBtn', response.data)

    def test_profile_api(self):
        # 1. Login with demo patient
        login_res = self.client.post('/api/auth/login', json={
            'email': 'patient@example.com',
            'password': 'password123'
        })
        self.assertEqual(login_res.status_code, 200)

        # 2. Get profile
        get_res = self.client.get('/api/user/profile')
        self.assertEqual(get_res.status_code, 200)
        p_data = json.loads(get_res.data)
        self.assertTrue(p_data['success'])
        self.assertEqual(p_data['profile']['email'], 'patient@example.com')

        # 3. Update profile with new avatar, blood group, allergies, address
        new_avatar = 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150'
        update_res = self.client.put('/api/user/profile', json={
            'name': 'Kalyan Kumar Updated',
            'phone': '9876543210',
            'age': 29,
            'gender': 'Male',
            'profile_pic': new_avatar,
            'blood_group': 'B+',
            'emergency_contact': '9876543299 (Spouse)',
            'address': 'Hitec City, Hyderabad',
            'allergies': 'Aspirin, Penicillin',
            'medical_history': 'Mild allergic asthma'
        })
        self.assertEqual(update_res.status_code, 200)
        up_data = json.loads(update_res.data)
        self.assertTrue(up_data['success'])
        self.assertEqual(up_data['profile']['profile_pic'], new_avatar)
        self.assertEqual(up_data['profile']['blood_group'], 'B+')
        self.assertEqual(up_data['profile']['allergies'], 'Aspirin, Penicillin')

    def test_three_hour_advance_booking_rule(self):
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # 1. Attempt slot in the immediate past or within 1 hour -> MUST BE REJECTED
        immediate_slot_time = (now + datetime.timedelta(minutes=30)).strftime("%I:%M %p")
        res_immediate = self.client.post('/api/appointments', json={
            'doctor_id': 1,
            'patient_name': 'Test Advance Rule',
            'patient_phone': '9876543210',
            'patient_age': 30,
            'patient_gender': 'Male',
            'appointment_date': today_str,
            'appointment_time': immediate_slot_time,
            'problem_description': 'Immediate appointment'
        })
        self.assertEqual(res_immediate.status_code, 400)
        imm_data = json.loads(res_immediate.data)
        self.assertTrue(imm_data.get('lead_time_violation'))
        self.assertIn('3 hours in advance', imm_data['message'])

        # 2. Attempt slot 2 days in advance -> MUST BE CONFIRMED
        future_date = (now + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        res_future = self.client.post('/api/appointments', json={
            'doctor_id': 1,
            'patient_name': 'Test Advance Rule Future',
            'patient_phone': '9876543210',
            'patient_age': 30,
            'patient_gender': 'Male',
            'appointment_date': future_date,
            'appointment_time': '10:00 AM',
            'problem_description': 'Routine consultation'
        })
        self.assertEqual(res_future.status_code, 200)
        fut_data = json.loads(res_future.data)
        self.assertTrue(fut_data['success'])
        self.assertTrue(fut_data['appointment']['appointment_number'].startswith('MED-APT-'))

    def test_ai_universal_medicine_search(self):
        # 1. Search for global brand 'Adderall'
        res1 = self.client.get('/api/medicines?q=Adderall')
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.data)
        self.assertTrue(data1['success'])
        self.assertGreater(data1['count'], 0)
        med1 = data1['medicines'][0]
        self.assertIn('Adderall', med1['brand_name'])
        self.assertTrue(len(med1['how_it_works']) > 0)
        self.assertTrue(len(med1['dosage_instructions']) > 0)

        # 2. Search for global biologic 'Humira'
        res2 = self.client.get('/api/medicines?q=Humira')
        self.assertEqual(res2.status_code, 200)
        data2 = json.loads(res2.data)
        self.assertTrue(data2['success'])
        med2 = data2['medicines'][0]
        self.assertIn('Humira', med2['brand_name'])
        self.assertIn('Adalimumab', med2['generic_name'])

        # 3. Search for any international pharmaceutical name 'Trastuzumab'
        res3 = self.client.get('/api/medicines?q=Trastuzumab')
        self.assertEqual(res3.status_code, 200)
        data3 = json.loads(res3.data)
        self.assertTrue(data3['success'])
        self.assertGreater(data3['count'], 0)
        med3 = data3['medicines'][0]
        self.assertIn('Trastuzumab', med3['name'])
        self.assertTrue(len(med3['uses_detailed']) > 0)

    def test_doctors_count_and_specialties(self):
        res = self.client.get('/api/doctors')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertGreaterEqual(data['count'], 18)

        # Check oncology and nephrology specialists are included
        specialties = [d['specialty'] for d in data['doctors']]
        self.assertTrue(any('Oncologist' in s for s in specialties))
        self.assertTrue(any('Nephrologist' in s for s in specialties))
        self.assertTrue(any('Endocrinologist' in s for s in specialties))

    def test_symptom_checker_english(self):
        res = self.client.post('/api/symptom-check', json={
            'symptoms': 'severe high fever and continuous headache'
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('General Physician', data['recommended_specialties'])
        self.assertTrue(len(data['guidance']) > 0)

    def test_ai_chat_features(self):
        # 1. Empty message error
        res_empty = self.client.post('/api/ai-chat', json={'message': ''})
        self.assertEqual(res_empty.status_code, 400)

        # 2. Greeting
        res_hi = self.client.post('/api/ai-chat', json={'message': 'hello doctor'})
        self.assertEqual(res_hi.status_code, 200)
        hi_data = json.loads(res_hi.data)
        self.assertTrue(hi_data['success'])
        self.assertIn('AarogyaPlus AI', hi_data['reply'])

        # 3. Symptom triage in chat
        res_sym = self.client.post('/api/ai-chat', json={'message': 'I have severe cough and throat pain for 3 days'})
        self.assertEqual(res_sym.status_code, 200)
        sym_data = json.loads(res_sym.data)
        self.assertTrue(sym_data['success'])
        self.assertIn('Pulmonologist', sym_data['reply'])

        # 4. Medicine lookup in chat
        res_med = self.client.post('/api/ai-chat', json={'message': 'What is Ozempic used for?'})
        self.assertEqual(res_med.status_code, 200)
        med_data = json.loads(res_med.data)
        self.assertTrue(med_data['success'])
        self.assertIn('Ozempic', med_data['reply'])
        self.assertTrue(any(a['type'] == 'view_medicine' for a in med_data['actions']))

        # 5. Doctor recommendation in chat
        res_doc = self.client.post('/api/ai-chat', json={'message': 'Find me a cardiologist for heart checkup'})
        self.assertEqual(res_doc.status_code, 200)
        doc_data = json.loads(res_doc.data)
        self.assertTrue(doc_data['success'])
        self.assertIn('Cardiologist', doc_data['reply'])
        self.assertTrue(any(a['type'] == 'book_doctor' for a in doc_data['actions']))

        # 6. Emergency red flag in chat
        res_emg = self.client.post('/api/ai-chat', json={'message': 'Patient has severe chest pain radiating to arm and difficulty breathing'})
        self.assertEqual(res_emg.status_code, 200)
        emg_data = json.loads(res_emg.data)
        self.assertTrue(emg_data['success'])
        self.assertTrue(emg_data['emergency'])
        self.assertIn('108', emg_data['reply'])

if __name__ == '__main__':
    unittest.main()
