from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import random
import json
import os
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here'
soz_verenler = []
kayitli_nickler = set()
soz_sayaci = 0
son_soz_tarihi = None

# Database simulation
if not os.path.exists('user_results.json'):
    with open('user_results.json', 'w') as f:
        json.dump([], f)

# Translation dictionaries
translations = {
    'tr': {
        'home': 'Ana Sayfa',
        'info': 'Bilgilendirme',
        'destek': 'Siteyi Destekle',
        'victims': 'Kurbanlar',
        'impact_test': 'Senin Etkin',
        'title': 'Çevresel Etki Testi',
        'subtitle': 'Günlük alışkanlıklarınızın dünyaya olan etkisini ölçün',
        'detailed_test_desc': '20 kapsamlı soru ile ayrıntılı rapor alın (12-15 dakika)',
        'select_test': 'Test Türünü Seçin',
        'quick_test': 'Hızlı Test',
        'quick_test_desc': '10 temel soru ile genel etkinizi ölçün (5-7 dakika)',
        'detailed_test': 'Detaylı Analiz',
        'start_test': 'Teste Başla',
        'results_title': 'Test Sonuçlarınız',
        'results_desc': 'Günlük alışkanlıklarınızın çevresel etkisi:',
        'recommendations': 'İyileştirme Önerileri',
        'game_title': 'Çevre Bilinci Oyunu',
        'game_desc': 'Eşleşen çevre dostu uygulamaları bulun ve puan kazanın!',
        'retake_test': 'Testi Yeniden Yap',
        'share_results': 'Sonuçları Paylaş',
        'download_report': 'Raporu İndir',
        'select_option': 'Seçiniz...',
        'hint_text': 'Her seçeneğin çevresel etkisi farklıdır',
        'privacy_policy': 'Gizlilik Politikası',
        'terms_of_use': 'Kullanım Şartları'
    },
    'en': {
        'home': 'Home',
        'info': 'Information',
        'victims': 'Victims',
        'impact_test': 'Impact Test',
        'title': 'Environmental Impact Test',
        'subtitle': 'Measure the impact of your daily habits on the world',
        'detailed_test_desc': 'Get a detailed report with 20 comprehensive questions (12-15 minutes)',
        'select_test': 'Select Test Type',
        'destek': 'Support Us',
        'quick_test': 'Quick Test',
        'quick_test_desc': 'Measure your general impact with 10 basic questions (5-7 minutes)',
        'detailed_test': 'Detailed Analysis',
        'start_test': 'Start Test',
        'results_title': 'Your Test Results',
        'results_desc': 'Environmental impact of your daily habits:',
        'recommendations': 'Improvement Recommendations',
        'game_title': 'Environmental Awareness Game',
        'game_desc': 'Find matching eco-friendly practices and earn points!',
        'retake_test': 'Retake Test',
        'share_results': 'Share Results',
        'download_report': 'Download Report',
        'select_option': 'Select...',
        'hint_text': 'Each option has different environmental impact',
        'privacy_policy': 'Privacy Policy',
        'terms_of_use': 'Terms of Use'
    }
}

# Enhanced question data with more realistic weights and impact calculations
question_data = {
    "transportation": {
        "weight": 1.8,
        "questions": [0, 5, 11, 19],
        "impact_factor": 4200
    },
    "nutrition": {
        "weight": 1.7,
        "questions": [1, 8, 15, 16],
        "impact_factor": 3800
    },
    "energy": {
        "weight": 1.5,
        "questions": [2, 6, 7],
        "impact_factor": 3200
    },
    "waste": {
        "weight": 1.4,
        "questions": [3, 10, 14, 17, 18],
        "impact_factor": 2800
    },
    "consumption": {
        "weight": 1.3,
        "questions": [4, 9, 13],
        "impact_factor": 2400
    },
    "lifestyle": {
        "weight": 1.2,
        "questions": [12],
        "impact_factor": 2000
    }
}

def calculate_averages():
    try:
        with open('user_results.json', 'r') as f:
            results = json.load(f)
            
        if not results:
            return {
                "average_score": 58,
                "top_10_score": 82,
                "category_averages": {
                    "transportation": 52,
                    "nutrition": 60,
                    "energy": 55,
                    "waste": 48,
                    "consumption": 51,
                    "lifestyle": 45
                }
            }
            
        total_score = 0
        category_scores = defaultdict(list)
        
        for result in results:
            total_score += result['score']
            for category, score in result['category_scores'].items():
                category_scores[category].append(score)
        
        average_score = round(total_score / len(results))
        sorted_scores = sorted([r['score'] for r in results], reverse=True)
        top_10_index = len(sorted_scores) // 10
        top_10_score = sorted_scores[top_10_index] if top_10_index > 0 else sorted_scores[0]
        
        category_averages = {}
        for category, scores in category_scores.items():
            category_averages[category] = round(sum(scores) / len(scores))
        
        return {
            "average_score": average_score,
            "top_10_score": top_10_score,
            "category_averages": category_averages
        }
    except:
        return {
            "average_score": 58,
            "top_10_score": 82,
            "category_averages": {
                "transportation": 52,
                "nutrition": 60,
                "energy": 55,
                "waste": 48,
                "consumption": 51,
                "lifestyle": 45
            }
        }



def validate_answers(answers):
    for key, value in answers.items():
        if not key.startswith('soru'):
            return False
        if not value.isdigit() or int(value) < 0 or int(value) > 4:
            return False
    return True

def save_user_results(score, category_scores, test_type):
    try:
        with open('user_results.json', 'r') as f:
            try:
                results = json.load(f)
            except json.JSONDecodeError:
                results = []
    except FileNotFoundError:
        results = []
    
    try:
        results.append({
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "category_scores": category_scores,
            "test_type": test_type
        })
        
        with open('user_results.json', 'w') as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        app.logger.error(f"Error saving user results: {str(e)}")
def calculate_carbon_footprint(category_scores):
    total_footprint = 0
    category_footprints = {}
    
    for category, data in question_data.items():
        impact = (100 - category_scores[category]) * data["impact_factor"] / 100
        weighted_impact = impact * data["weight"]
        category_footprints[category] = round(weighted_impact, 1)
        total_footprint += weighted_impact
    
    total_footprint = round(total_footprint / 1000, 1)  # Convert to tons
    
    # Calculate normalized percentages
    percentages = {}
    if total_footprint > 0:
        # First calculate raw percentages
        raw_percentages = {}
        total_raw = 0
        for category in category_footprints:
            raw_percent = (category_footprints[category] / total_footprint) * 100
            raw_percentages[category] = raw_percent
            total_raw += raw_percent
        
        # Normalize to ensure they sum to 100%
        normalized_total = 0
        remaining_percent = 100
        categories = list(category_footprints.keys())
        
        for i, category in enumerate(categories):
            if i == len(categories) - 1:
                # Last category gets remaining percentage
                percentages[category] = round(remaining_percent)
            else:
                percent = round(raw_percentages[category] / total_raw * 100)
                percentages[category] = percent
                remaining_percent -= percent
                normalized_total += percent
    
    return total_footprint, percentages

def calculate_electricity_consumption(answers):
    base = 420  # kWh/month
    modifiers = {
        'soru3': 35,   # Energy efficient appliances
        'soru7': 25,   # Turning off devices
        'soru8': 20,   # Device usage time
        'soru17': 30   # Device replacement frequency
    }
    
    total = base
    for q, mod in modifiers.items():
        total -= int(answers.get(q, 2)) * mod
    
    return max(180, round(total))  # Realistic minimum

def calculate_water_consumption(answers):
    base = 185  # liters/day
    modifier = int(answers.get('soru13', 2)) * 25
    return base - modifier

def calculate_waste_production(answers):
    base = 8.5  # kg/week
    modifiers = {
        'soru4': 1.2,    # Recycling
        'soru9': 0.9,  # Eating out
        'soru11': 1.1, # Plastic avoidance
        'soru15': 1.3, # Waste production
        'soru18': 1.0  # Water bottles
    }
    
    total = base
    for q, mod in modifiers.items():
        total -= int(answers.get(q, 2)) * mod
    
    return round(max(2.5, total), 1)

def generate_recommendations(answers, current_lang):
    recommendations = []
    
    # Transportation recommendations
    transport_score = sum(int(answers.get(f'soru{q+1}', 2)) for q in question_data["transportation"]["questions"])
    if transport_score > 8:
        recs = [
            ("Toplu taşıma veya bisiklet kullanımını artırarak ulaşım kaynaklı karbon ayak izinizi %40'a kadar azaltabilirsiniz.",
             "Increase public transportation or bicycle usage to reduce your transportation carbon footprint by up to 40%."),
            ("Uçakla seyahatlerinizi azaltmayı veya karbon dengeleme programlarına katılmayı düşünün. Bir transatlantik uçuş 2-3 ton CO₂ emisyonuna neden olur.",
             "Consider reducing air travel or participating in carbon offset programs. A transatlantic flight causes 2-3 tons of CO₂ emissions."),
            ("Elektrikli araç kullanarak emisyonlarınızı %60-80 oranında düşürebilirsiniz.",
             "You can reduce emissions by 60-80% by using electric vehicles.")
        ]
        recommendations.extend([rec[0] if current_lang == 'tr' else rec[1] for rec in recs[:2]])
    
    # Nutrition recommendations
    nutrition_score = sum(int(answers.get(f'soru{q+1}', 2)) for q in question_data["nutrition"]["questions"])
    if nutrition_score > 8:
        recs = [
            ("Kırmızı et tüketiminizi haftada 1-2 öğünle sınırlandırmayı düşünün. 1 kg sığır eti 35 kg CO₂ emisyonuna neden olur.",
             "Consider limiting your red meat consumption to 1-2 meals per week. 1kg of beef causes 35kg of CO₂ emissions."),
            ("Yerel ve mevsimsel ürünler tüketerek gıda kaynaklı karbon ayak izinizi %25-40 azaltabilirsiniz.",
             "Reduce your food carbon footprint by 25-40% by consuming local and seasonal products."),
            ("Gıda israfını önlemek için daha küçük porsiyonlar hazırlayın. Dünyada üretilen gıdanın 1/3'ü israf ediliyor.",
             "Prepare smaller portions and use leftovers to prevent food waste. 1/3 of all food produced globally is wasted.")
        ]
        recommendations.extend([rec[0] if current_lang == 'tr' else rec[1] for rec in recs[:2]])
    
    # Energy recommendations
    energy_score = sum(int(answers.get(f'soru{q+1}', 2)) for q in question_data["energy"]["questions"])
    if energy_score > 6:
        recs = [
            ("Enerji tasarruflu ampuller ve A+++ cihazlar kullanarak elektrik tüketiminizi %50'ye kadar azaltabilirsiniz.",
             "Reduce your electricity consumption by up to 50% by using energy-saving bulbs and A+++ appliances."),
            ("Kullanmadığınız cihazları tamamen kapatarak yılda 150-250 kWh tasarruf sağlayabilirsiniz.",
             "Save 150-250 kWh per year by completely turning off devices you're not using."),
            ("Güneş enerjisi sistemleri kullanarak enerji tüketiminizi sürdürülebilir hale getirebilirsiniz. 5kW'lık bir sistem yılda 6-8 ton CO₂ tasarrufu sağlar.",
             "Consider using solar energy systems to make your energy consumption sustainable. A 5kW system saves 6-8 tons of CO₂ annually.")
        ]
        recommendations.extend([rec[0] if current_lang == 'tr' else rec[1] for rec in recs[:2]])
    
    # Waste recommendations
    waste_score = sum(int(answers.get(f'soru{q+1}', 2)) for q in question_data["waste"]["questions"])
    if waste_score > 10:
        recs = [
            ("Geri dönüşüm programlarına katılarak atık üretiminizi %60'a kadar azaltabilirsiniz.",
             "Reduce your waste production by up to 60% by participating in recycling programs."),
            ("Plastik poşetler yerine bez çantalar kullanmayı deneyin. Bir plastik poşetin doğada çözünmesi 1000 yıl sürer.",
             "Try using cloth bags instead of plastic bags. A plastic bag takes 1000 years to decompose."),
            ("Tek kullanımlık ürünler yerine yeniden kullanılabilir alternatifleri tercih edin. Örneğin, cam şişeler kullanın.",
             "Prefer reusable alternatives to disposable products. For example, use glass bottles."),
            ("Kompost yaparak organik atıklarınızı değerlendirebilirsiniz. Evsel atıkların %40-50'si kompostlanabilir.",
             "You can utilize 40-50% of household waste by composting.")
        ]
        recommendations.extend([rec[0] if current_lang == 'tr' else rec[1] for rec in recs[:3]])
    
    # Ensure we have at least 5 recommendations
    default_recs = [
        ("Karbon ayak izinizi dengelemek için ağaç dikme projelerine destek olabilirsiniz. Bir ağaç yılda 25 kg CO₂ emer.",
         "You can support tree planting projects to offset your carbon footprint. One tree absorbs 25kg of CO₂ annually."),
        ("Yürüyerek veya bisikletle ulaşımı tercih ederek hem sağlığınıza hem de çevreye katkı sağlayabilirsiniz. 5 km'lik bir araba yolculuğu 1.2 kg CO₂ üretirken, bisiklet sıfır emisyon üretir.",
         "You can contribute to both your health and the environment by preferring walking or cycling. A 5km car trip produces 1.2kg CO₂ while cycling produces zero emissions."),
        ("Su tasarruflu cihazlar kullanarak hem çevreyi koruyabilir hem de faturalarınızı %40'a kadar düşürebilirsiniz.",
         "You can both protect the environment and reduce your bills by up to 40% using water-saving devices.")
    ]
    
    while len(recommendations) < 5:
        rec = default_recs[len(recommendations) % len(default_recs)]
        recommendations.append(rec[0] if current_lang == 'tr' else rec[1])
    
    return recommendations[:7]  # Return max 7 recommendations

def determine_badges(score, category_scores, current_lang):
    badges = []
    
    if score >= 85:
        badges.append({
            "name": "Eco Champion" if current_lang == 'en' else "Çevre Şampiyonu",
            "icon": "fa-trophy",
            "color": "var(--accent)",
            "description": "Top 5% of environmentally friendly users" if current_lang == 'en' else "Çevre dostu kullanıcıların en iyi %5'i"
        })
    
    if category_scores.get("transportation", 0) >= 85:
        badges.append({
            "name": "Green Commuter" if current_lang == 'en' else "Yeşil Yolcu",
            "icon": "fa-bicycle",
            "color": "var(--primary)",
            "description": "Excellent transportation habits" if current_lang == 'en' else "Mükemmel ulaşım alışkanlıkları"
        })
    
    if category_scores.get("waste", 0) >= 90:
        badges.append({
            "name": "Recycling Expert" if current_lang == 'en' else "Geri Dönüşüm Uzmanı",
            "icon": "fa-recycle",
            "color": "var(--success)",
            "description": "Outstanding waste management" if current_lang == 'en' else "Üstün atık yönetimi"
        })
    
    if category_scores.get("energy", 0) >= 80:
        badges.append({
            "name": "Energy Saver" if current_lang == 'en' else "Enerji Koruyucu",
            "icon": "fa-bolt",
            "color": "var(--secondary)",
            "description": "Exceptional energy conservation" if current_lang == 'en' else "Olağanüstü enerji koruma"
        })
    
    if not badges:  # Default badge if no others earned
        badges.append({
            "name": "Climate Aware" if current_lang == 'en' else "İklim Bilinçli",
            "icon": "fa-leaf",
            "color": "var(--primary-light)",
            "description": "Taking first steps towards sustainability" if current_lang == 'en' else "Sürdürülebilirlik için ilk adımlar"
        })
    
    return badges

@app.route("/", methods=["GET", "POST"])
def index():
    global soz_sayaci, son_soz_tarihi
    current_lang = session.get('lang', 'en')
    
    if request.method == "POST":
        nick = request.form["nick"].strip()
        mesaj = request.form["mesaj"].strip()
        if nick and nick not in kayitli_nickler:
            soz_sayaci += 1
            zaman = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            soz_verenler.append({"nick": nick, "mesaj": mesaj, "tarih": zaman})
            kayitli_nickler.add(nick)
            son_soz_tarihi = zaman
        return redirect(url_for("index"))
    
    son_bes_kisi = list(reversed(soz_verenler[-5:]))
    return render_template("index.html", 
                         soz_sayaci=soz_sayaci, 
                         son_soz_tarihi=son_soz_tarihi, 
                         son_bes_kisi=son_bes_kisi,
                         current_lang=current_lang,
                         t=translations[current_lang])
@app.route("/destek")
def destek():
    current_lang = session.get('lang', 'tr')
    return render_template("destek.html", current_lang=current_lang, t=translations[current_lang])

@app.route("/bilgilendirme")
def bilgilendirme():
    current_lang = session.get('lang', 'en')
    return render_template("bilgi.html", current_lang=current_lang, t=translations[current_lang])

@app.route("/kurbanlar")
def kurbanlar():
    current_lang = session.get('lang', 'en')
    return render_template("kurbanlar.html", current_lang=current_lang, t=translations[current_lang])

@app.route("/senin-etkin", methods=["GET", "POST"])
def senin_etkin():
    sonuc = None
    test_turu = None
    current_lang = session.get('lang', 'en')
    
    if request.method == "POST":
        # Test type selection form
        if 'test_turu' in request.form and request.form.get('answers_submitted') == 'false':
            test_turu = request.form.get("test_turu")
            return render_template("senin_etkin.html", 
                                test_turu=test_turu, 
                                sonuc=sonuc,
                                current_lang=current_lang,
                                t=translations[current_lang])
        
        # Test answers submission
        if request.form.get('answers_submitted') == 'true':
            test_turu = request.form.get("test_turu")
            
            answers = {}
            for key, value in request.form.items():
                if key.startswith('soru'):
                    answers[key] = value
            
            # Calculate scores for each category
            category_scores = {}
            category_weights = {}
            
            for category, data in question_data.items():
                question_values = []
                for q_idx in data['questions']:
                    if f'soru{q_idx+1}' in answers:
                        question_values.append(int(answers[f'soru{q_idx+1}']))
                
                if question_values:
                    avg_score = sum(question_values) / len(question_values)
                    category_scores[category] = 100 - (avg_score * 25)
                    category_weights[category] = data['weight']
                else:
                    category_scores[category] = 50
                    category_weights[category] = 1.0
            
            # Calculate overall weighted score
            total_weight = sum(category_weights.values())
            weighted_sum = sum(category_scores[cat] * category_weights[cat] for cat in category_scores)
            puan = round(weighted_sum / total_weight)
            
            # Score evaluation
            if current_lang == 'tr':
                if puan >= 85:
                    puan_text = "Çevre Dostu"
                    aciklama = "Mükemmel! Çevre dostu yaşam tarzınızla örnek oluyorsunuz."
                elif puan >= 70:
                    puan_text = "İyi"
                    aciklama = "İyi bir noktadasınız ancak bazı alanlarda daha iyi olabilirsiniz."
                elif puan >= 50:
                    puan_text = "Orta"
                    aciklama = "Ortalama bir çevresel etkiniz var. İyileştirme için önerilerimize göz atın."
                elif puan >= 30:
                    puan_text = "Geliştirilebilir"
                    aciklama = "Çevresel etkinizi azaltmak için önemli değişiklikler yapmalısınız."
                else:
                    puan_text = "Yüksek Etki"
                    aciklama = "Çevresel etkiniz çok yüksek. Acilen önlem almalısınız."
            else:
                if puan >= 85:
                    puan_text = "Eco-Friendly"
                    aciklama = "Excellent! You're setting an example with your eco-friendly lifestyle."
                elif puan >= 70:
                    puan_text = "Good"
                    aciklama = "You're doing well but could improve in some areas."
                elif puan >= 50:
                    puan_text = "Average"
                    aciklama = "You have an average environmental impact. Check our recommendations for improvement."
                elif puan >= 30:
                    puan_text = "Needs Improvement"
                    aciklama = "You should make significant changes to reduce your environmental impact."
                else:
                    puan_text = "High Impact"
                    aciklama = "Your environmental impact is very high. You need to take urgent action."
            
            # Calculate statistics
            yillik_karbon, carbon_percentages = calculate_carbon_footprint(category_scores)
            aylik_elektrik = calculate_electricity_consumption(answers)
            gunluk_su = calculate_water_consumption(answers)
            haftalik_cop = calculate_waste_production(answers)
            
            # Generate recommendations
            tavsiyeler = generate_recommendations(answers, current_lang)
            
            # Determine earned badges
            badges = determine_badges(puan, category_scores, current_lang)
            
            # Get community averages
            averages = calculate_averages()
            
            # Prepare category names and descriptions
            if current_lang == 'tr':
                kategori_adlari = {
                    "transportation": "Ulaşım",
                    "nutrition": "Beslenme",
                    "energy": "Enerji",
                    "waste": "Atık Yönetimi",
                    "consumption": "Tüketim",
                    "lifestyle": "Yaşam Tarzı"
                }
                
                kategori_aciklamalari = {
                    "transportation": f"Ulaşım alışkanlıklarınız {averages['category_averages']['transportation']} ortalamasına kıyasla {category_scores['transportation']:.0f} puan aldı. Ortalama bir kişi yılda 3-4 ton CO₂ üretirken, siz {yillik_karbon * 0.3:.1f} ton üretiyorsunuz.",
                    "nutrition": f"Beslenme alışkanlıklarınız {averages['category_averages']['nutrition']} ortalamasına kıyasla {category_scores['nutrition']:.0f} puan aldı. Vegan beslenme karbon ayak izini %60-80 oranında azaltabilir.",
                    "energy": f"Enerji kullanımınız {averages['category_averages']['energy']} ortalamasına kıyasla {category_scores['energy']:.0f} puan aldı. Aylık ortalama {aylik_elektrik} kWh elektrik tüketiyorsunuz.",
                    "waste": f"Atık yönetiminiz {averages['category_averages']['waste']} ortalamasına kıyasla {category_scores['waste']:.0f} puan aldı. Haftalık {haftalik_cop} kg atık üretiyorsunuz.",
                    "consumption": f"Tüketim alışkanlıklarınız {averages['category_averages']['consumption']} ortalamasına kıyasla {category_scores['consumption']:.0f} puan aldı. Sürdürülebilir ürünler karbon ayak izinizi önemli ölçüde azaltabilir.",
                    "lifestyle": f"Yaşam tarzınız {averages['category_averages']['lifestyle']} ortalamasına kıyasla {category_scores['lifestyle']:.0f} puan aldı. Küçük değişikliklerle büyük farklar yaratabilirsiniz."
                }
            else:
                kategori_adlari = {
                    "transportation": "Transportation",
                    "nutrition": "Nutrition",
                    "energy": "Energy",
                    "waste": "Waste Management",
                    "consumption": "Consumption",
                    "lifestyle": "Lifestyle"
                }
                
                kategori_aciklamalari = {
                    "transportation": f"Your transportation habits scored {category_scores['transportation']:.0f} compared to the average of {averages['category_averages']['transportation']}. While an average person produces 3-4 tons of CO₂ annually, you produce {yillik_karbon * 0.3:.1f} tons.",
                    "nutrition": f"Your eating habits scored {category_scores['nutrition']:.0f} compared to the average of {averages['category_averages']['nutrition']}. A vegan diet can reduce carbon footprint by 60-80%.",
                    "energy": f"Your energy usage scored {category_scores['energy']:.0f} compared to the average of {averages['category_averages']['energy']}. Your monthly electricity consumption is {aylik_elektrik} kWh.",
                    "waste": f"Your waste management scored {category_scores['waste']:.0f} compared to the average of {averages['category_averages']['waste']}. You produce {haftalik_cop} kg of waste weekly.",
                    "consumption": f"Your consumption habits scored {category_scores['consumption']:.0f} compared to the average of {averages['category_averages']['consumption']}. Sustainable products can significantly reduce your carbon footprint.",
                    "lifestyle": f"Your lifestyle scored {category_scores['lifestyle']:.0f} compared to the average of {averages['category_averages']['lifestyle']}. Small changes can make big differences."
                }
            
            # Prepare results for template
            sonuc = {
                "puan": puan,
                "puan_text": puan_text,
                "aciklama": aciklama,
                "kategori_puanlari": {
                    kategori_adlari["transportation"]: round(category_scores["transportation"]),
                    kategori_adlari["nutrition"]: round(category_scores["nutrition"]),
                    kategori_adlari["energy"]: round(category_scores["energy"]),
                    kategori_adlari["waste"]: round(category_scores["waste"]),
                    kategori_adlari["consumption"]: round(category_scores["consumption"]),
                    kategori_adlari["lifestyle"]: round(category_scores["lifestyle"])
                },
                "kategori_aciklamalari": {
                    kategori_adlari["transportation"]: kategori_aciklamalari["transportation"],
                    kategori_adlari["nutrition"]: kategori_aciklamalari["nutrition"],
                    kategori_adlari["energy"]: kategori_aciklamalari["energy"],
                    kategori_adlari["waste"]: kategori_aciklamalari["waste"],
                    kategori_adlari["consumption"]: kategori_aciklamalari["consumption"],
                    kategori_adlari["lifestyle"]: kategori_aciklamalari["lifestyle"]
                },
                "tavsiyeler": tavsiyeler,
                "yillik_karbon": yillik_karbon,
                "aylik_elektrik": aylik_elektrik,
                "gunluk_su": gunluk_su,
                "haftalik_cop": haftalik_cop,
                "community_average": averages["average_score"],
                "top_10_score": averages["top_10_score"],
                "category_averages": averages["category_averages"],
                "carbon_percentages": carbon_percentages,
                "badges": badges,
                "averages": averages
                
            }
            
            # Save results to "database"
            save_user_results(puan, category_scores, test_turu)
    
    return render_template("senin_etkin.html", 
                         test_turu=test_turu, 
                         sonuc=sonuc,
                         current_lang=current_lang,
                         t=translations[current_lang],
                         carbon_data=json.dumps(sonuc['carbon_percentages']) if sonuc else '{}',
                         averages_data=json.dumps(sonuc['averages']['category_averages']) if sonuc else '{}')
                        
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in translations:
        session['lang'] = lang
        session.permanent = True
        # Dil değiştikten sonra bir önceki sayfaya yönlendir
        referrer = request.referrer or url_for('index')
        return redirect(referrer)
    return redirect(url_for('index'))

@app.route("/privacy-policy")
def privacy_policy():
    current_lang = session.get('lang', 'en')
    return render_template("privacy_policy.html", current_lang=current_lang, t=translations[current_lang])

@app.route("/terms-of-use")
def terms_of_use():
    current_lang = session.get('lang', 'en')
    return render_template("terms_of_use.html", current_lang=current_lang, t=translations[current_lang])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)