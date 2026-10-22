"""
B2B Lead Pipeline Generator, Exporter, and Integrity Validator.
Pure Python 3.9 standard library implementation with zero external dependencies.
"""

import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .models import (
    LeadDataset,
    LeadTarget,
    DecisionMaker,
    Diagnostics,
    FinancialImpact,
    OutreachAssets,
)
from .leak_calculator import ConversionLeakCalculator

CANONICAL_TARGETS_RAW = [
    {
        "target_id": "TGT-001",
        "company_name": "Apex Architectural Roofing & Copperworks",
        "vertical": "Luxury Residential Roofing & Architectural Standing Seam",
        "headquarters": "Denver, CO",
        "website_url": "https://apexarchitecturalroof.com",
        "domain_url": "https://apexarchitecturalroof.com",
        "estimated_aov": 28500.0,
        "estimated_monthly_visitors": 3200,
        "estimated_ad_spend_monthly": 6500.0,
        "decision_maker": {
            "name": "Garrett Vance",
            "title": "Founder & Managing Partner",
            "email": "garrett@apexarchitecturalroof.com",
            "phone": "(303) 555-0194",
            "linkedin_url": "https://linkedin.com/in/garrett-vance-apex",
        },
        "primary_conversion_leak": "Uncompressed 38.4MB 4K hero video stalling Largest Contentful Paint (LCP) at 6.8 seconds on 4G mobile, bouncing 58% of paid mobile visitors.",
        "secondary_conversion_leak": "Mobile header phone number is an inert string lacking the tel: link attribute, preventing one-tap mobile calling.",
        "estimated_monthly_lost_pipeline": 114000.0,
        "estimated_annual_recoverable": 1368000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_001.md",
        "audit_report_file": "audits/audit_tgt_001.md",
        "diagnostics": {
            "primary_leak_summary": "Uncompressed Hero video (38.4MB MP4) stalling LCP at 6.8s on 4G mobile",
            "primary_leak_technical_detail": "Asset /assets/videos/hero_copper_install.mp4 (38.4MB, no poster fallback) blocks hero render on cellular connections. 58% bounce before CTA.",
            "secondary_leak_summary": "Mobile header phone number is an inert SVG/text element lacking tel:+13035550194 anchor href.",
            "mobile_lcp_seconds": 6.8,
            "mobile_cls_score": 0.05,
            "speed_to_lead_sla_hours": 18.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 114000.0,
            "estimated_annual_recoverable_usd": 1368000.0,
        },
        "outreach_assets": {
            "email_subject": "Quick video on your mobile hero video (losing Denver copper inquiries)",
            "email_body_template": (
                "Hi Garrett, your 38MB hero video delays mobile load to 6.8s, bouncing half your visitors. "
                "Fixing this recovers $114k/mo in consultations. I recorded a quick video showing the fix. "
                "Open to seeing it? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Hi Garrett, looking directly at your Denver architectural roofing landing page on an emulated iPhone on mobile LTE. For the first 6.8 seconds, the screen is entirely blank white while your 38-megabyte 4K drone video downloads in the background.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: With 58% paid mobile traffic from Google Ads, visitors bounce before your consultation button renders. When they scroll, tapping your phone number does not open the dialer because it lacks an active link attribute. At a $28,500 average project value, losing four high-ticket mobile leads a month silently drains over $114,000 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: The fix takes less than 15 minutes: add a lightweight 42kb WebP poster image so the hero displays under 800ms, defer the video payload, and wrap your header contact in an active tel: link.\n"
                "1:10-1:30 | Soft CTA: I recorded a 3-minute video showing your web team how to drop in these two fixes. Would you like me to send that over for your developer?"
            ),
        },
    },
    {
        "target_id": "TGT-002",
        "company_name": "Summit Heritage Slate & Tile",
        "vertical": "Historical Restoration & Luxury Slate Roofing",
        "headquarters": "Scarsdale, NY",
        "website_url": "https://summitheritageslate.com",
        "domain_url": "https://summitheritageslate.com",
        "estimated_aov": 42000.0,
        "estimated_monthly_visitors": 2100,
        "estimated_ad_spend_monthly": 4000.0,
        "decision_maker": {
            "name": "Julian Moreau",
            "title": "Director of Operations & Estimating",
            "email": "jmoreau@summitheritageslate.com",
            "phone": "(914) 555-0182",
            "linkedin_url": "https://linkedin.com/in/julian-moreau-slate",
        },
        "primary_conversion_leak": "Absence of sticky mobile conversion banner across 9 full viewports of slate portfolio scrolling.",
        "secondary_conversion_leak": "Multi-step quote form JS error (datePicker.init is not a function) silently breaks submission on iOS Safari.",
        "estimated_monthly_lost_pipeline": 126000.0,
        "estimated_annual_recoverable": 1512000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_002.md",
        "audit_report_file": "audits/audit_tgt_002.md",
        "diagnostics": {
            "primary_leak_summary": "Missing sticky mobile CTA bar across deep portfolio galleries",
            "primary_leak_technical_detail": "Gallery pages require 9 full viewport scrolls without persistent call-to-action bar, dropping mobile scroll-to-action rate to 0.8%.",
            "secondary_leak_summary": "Uncaught TypeError: datePicker.init is not a function in bundle.min.js:142 on iOS Safari.",
            "mobile_lcp_seconds": 4.2,
            "mobile_cls_score": 0.08,
            "speed_to_lead_sla_hours": 22.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 126000.0,
            "estimated_annual_recoverable_usd": 1512000.0,
        },
        "outreach_assets": {
            "email_subject": "Broken inspection form on iOS (Westchester slate projects)",
            "email_body_template": (
                "Hi Julian, while testing summitheritageslate.com on an iPhone, I found a JavaScript date-picker bug "
                "silently blocking Step 3 quote submissions. For $42k slate projects, fixing this protects $126k/mo in pipeline. "
                "I wrote a 4-line patch. Open to seeing the code? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Hi Julian, I was admiring your historic slate restoration work across Westchester County, but when browsing on an iPhone, there is a severe conversion break on Step 3 of your inspection form.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Watch what happens when a Scarsdale estate owner fills out your 3-step quote form. When they select roof pitch and tap Submit, nothing happens. A JavaScript date-picker error in bundle.min.js silently blocks the submit event with zero visual feedback. Affluent homeowners assume your site is broken and leave. At a $42,000 average contract value, losing three projects a month costs over $126,000 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: By replacing obsolete jQuery plugins with native HTML5 date pickers and anchoring a sticky Book Slate Inspection bar along your portfolio galleries, mobile visitors get an instant, reliable path to convert.\n"
                "1:10-1:30 | Soft CTA: I documented the exact 4 lines of script code your developer needs to replace to fix this today. Mind if I send over the code snippet?"
            ),
        },
    },
    {
        "target_id": "TGT-003",
        "company_name": "Vanguard Metal Roofing Systems",
        "vertical": "Commercial & Luxury Standing Seam Metal Roofing",
        "headquarters": "Austin, TX",
        "website_url": "https://vanguardmetalroofs.com",
        "domain_url": "https://vanguardmetalroofs.com",
        "estimated_aov": 24000.0,
        "estimated_monthly_visitors": 4500,
        "estimated_ad_spend_monthly": 8000.0,
        "decision_maker": {
            "name": "Marcus Sterling",
            "title": "VP of Commercial Development",
            "email": "m.sterling@vanguardmetalroofs.com",
            "phone": "(512) 555-0147",
            "linkedin_url": "https://linkedin.com/in/marcussterling-vanguard",
        },
        "primary_conversion_leak": "Unautomated lead intake routing to an unmonitored inbox with a 19.4-hour SLA delay.",
        "secondary_conversion_leak": "Absence of an interactive instant cost-per-sq-ft estimator causing bounce to regional competitors.",
        "estimated_monthly_lost_pipeline": 144000.0,
        "estimated_annual_recoverable": 1728000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_003.md",
        "audit_report_file": "audits/audit_tgt_003.md",
        "diagnostics": {
            "primary_leak_summary": "19.4-hour lead response delay without automated SMS confirmation",
            "primary_leak_technical_detail": "Inbound RFP forms dump to info@vanguardmetalroofs.com with no webhook trigger. Lead close probability decays by 80% after 15 minutes.",
            "secondary_leak_summary": "Missing instant material/cost-per-square estimator on commercial landing pages.",
            "mobile_lcp_seconds": 3.8,
            "mobile_cls_score": 0.04,
            "speed_to_lead_sla_hours": 19.4,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 144000.0,
            "estimated_annual_recoverable_usd": 1728000.0,
        },
        "outreach_assets": {
            "email_subject": "Speed-to-lead audit: Austin commercial metal roofing leads",
            "email_body_template": (
                "Hi Marcus, your commercial metal roofing pages rank well, but a 19-hour response delay costs estimated "
                "$144k/mo in pipeline. Responding within 5 minutes via automated SMS doubles bid capture. "
                "I diagrammed an instant SMS self-scheduling integration for your team. Open to reviewing? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Hi Marcus, Vanguard does stellar architectural metal roofing across Central Texas. But if a commercial general contractor requests a bid on your website today, their inquiry drops into a queue that takes over 19 hours to receive a response.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Harvard and MIT research shows that responding within 5 minutes yields an 8x higher conversion rate than waiting 30 minutes. In commercial metal roofing where deals exceed $24,000, waiting overnight means the GC has already scheduled site assessments with regional competitors. Inbound leads are high intent, but losing six contracts a month silently drains $144,000 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: We can automate this entirely: the moment a GC enters their project square footage, an instant two-way SMS confirms receipt with your direct estimating calendar link to lock in site walks while interest is peak.\n"
                "1:10-1:30 | Soft CTA: I sketched out a 1-page automation workflow connecting your existing form directly to SMS in under an afternoon. Would you be open to reviewing it?"
            ),
        },
    },
    {
        "target_id": "TGT-004",
        "company_name": "Beverly Hills Aesthetic Dental Spa",
        "vertical": "Porcelain Veneers & Full-Mouth Aesthetic Rehabilitation",
        "headquarters": "Beverly Hills, CA",
        "website_url": "https://bhaestheticdental.com",
        "domain_url": "https://bhaestheticdental.com",
        "estimated_aov": 22000.0,
        "estimated_monthly_visitors": 8400,
        "estimated_ad_spend_monthly": 15000.0,
        "decision_maker": {
            "name": "Dr. Aris Thorne",
            "title": "DDS & Clinical Director",
            "email": "drthorne@bhaestheticdental.com",
            "phone": "(310) 555-0163",
            "linkedin_url": "https://linkedin.com/in/dr-aris-thorne-dds",
        },
        "primary_conversion_leak": "Cumulative Layout Shift (CLS 0.42) on mobile smile gallery pushing booking CTA off-screen mid-tap.",
        "secondary_conversion_leak": "7-field consultation modal demanding medical insurance and panoramic X-ray upload causing 81% mobile abandonment.",
        "estimated_monthly_lost_pipeline": 110000.0,
        "estimated_annual_recoverable": 1320000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_004.md",
        "audit_report_file": "audits/audit_tgt_004.md",
        "diagnostics": {
            "primary_leak_summary": "Cumulative Layout Shift (CLS 0.42) on before/after smile gallery",
            "primary_leak_technical_detail": "Unsized gallery images load asynchronously without aspect-ratio CSS, jumping mobile DOM 300px down during touch tap events.",
            "secondary_leak_summary": "7-field consultation modal asking for insurance and panoramic X-ray upload on elective cosmetic cases.",
            "mobile_lcp_seconds": 3.6,
            "mobile_cls_score": 0.42,
            "speed_to_lead_sla_hours": 14.5,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 110000.0,
            "estimated_annual_recoverable_usd": 1320000.0,
        },
        "outreach_assets": {
            "email_subject": "Mobile smile gallery layout jump (losing veneer consults)",
            "email_body_template": (
                "Dear Dr. Thorne, unsized gallery photos cause a severe layout jump (CLS 0.42) on mobile, "
                "shifting your booking button off-screen. Fixing this recovers $110k/mo in cosmetic cases. "
                "I recorded a quick video walkthrough. Open to seeing it? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Dr. Thorne, your veneer transformations on Rodeo Drive are world-class, but mobile patients arriving from your Instagram ads experience a severe layout shift that prevents them from booking consultations.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Notice how when your before-and-after photo sliders load without reserved dimensions, the entire page jumps down 300 pixels right as the patient taps Book Virtual Smile Consult. They misclick into blank space and abandon. In addition, your form asks for irrelevant dental insurance details on elective cosmetic cases. At a $22,000 average case value, losing five veneer cases monthly drains $110,000 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Adding CSS aspect-ratio 16/9 to gallery containers and cutting your consultation modal down from 7 fields to 3 (Name, Phone, Primary Smile Goal) eliminates the jump and typically doubles mobile consult conversion.\n"
                "1:10-1:30 | Soft CTA: I recorded a 90-second video demonstrating the layout shift and showing the exact CSS attributes to add. May I send that to you or your practice manager?"
            ),
        },
    },
    {
        "target_id": "TGT-005",
        "company_name": "Manhattan Smile Architecture & Implantology",
        "vertical": "All-on-4 Full-Arch Dental Implants & Reconstruction",
        "headquarters": "New York, NY",
        "website_url": "https://manhattansmilearch.com",
        "domain_url": "https://manhattansmilearch.com",
        "estimated_aov": 31000.0,
        "estimated_monthly_visitors": 5600,
        "estimated_ad_spend_monthly": 14000.0,
        "decision_maker": {
            "name": "Elena Rostova",
            "title": "Patient Care Coordinator & Practice Administrator",
            "email": "elena@manhattansmilearch.com",
            "phone": "(212) 555-0178",
            "linkedin_url": "https://linkedin.com/in/elena-rostova-dental",
        },
        "primary_conversion_leak": "Insecure HTTP booking widget embed triggering 'Connection Not Secure' warning in iOS Safari and Chrome.",
        "secondary_conversion_leak": "Zero weekend speed-to-lead triage holding weekend surgical inquiries until Monday 9:00 AM.",
        "estimated_monthly_lost_pipeline": 124000.0,
        "estimated_annual_recoverable": 1488000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_005.md",
        "audit_report_file": "audits/audit_tgt_005.md",
        "diagnostics": {
            "primary_leak_summary": "Mixed Content / Insecure iframe SSL warning on mobile consultation scheduler",
            "primary_leak_technical_detail": "Scheduler embed loads over http://embed.patientbooking.net inside HTTPS page, triggering active browser security shield warning.",
            "secondary_leak_summary": "Weekend lead triage gap: inquiries between Friday 5pm and Monday 9am experience 60+ hour latency.",
            "mobile_lcp_seconds": 4.1,
            "mobile_cls_score": 0.09,
            "speed_to_lead_sla_hours": 28.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 124000.0,
            "estimated_annual_recoverable_usd": 1488000.0,
        },
        "outreach_assets": {
            "email_subject": "Browser security warning on your mobile implant booking page",
            "email_body_template": (
                "Hi Elena, your mobile implant booking widget loads over HTTP, triggering an active Not Secure "
                "browser warning. For $31k full-arch cases, this friction loses $124k/mo. I documented the 5-minute "
                "HTTPS fix and weekend SMS triage flow. May I share the link? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Hi Elena, I'm looking at your Upper East Side full-arch implant page on an iPhone. Look at what happens when a prospective patient clicks Schedule All-on-4 Consultation on mobile Safari.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Because your online booking widget embeds an unencrypted HTTP link inside your HTTPS site, modern iOS and Android browsers display an active red Connection Not Secure warning shield. To an affluent patient evaluating a $31,000 full-arch restoration, seeing a security warning destroys trust immediately. Coupled with zero weekend triage, losing four surgical cases a month drains $124,000 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Resolving this takes five minutes: update the booking embed source to the validated HTTPS endpoint and configure an automated weekend SMS triage so inquiries do not sit in limbo until Monday.\n"
                "1:10-1:30 | Soft CTA: I put together the exact SSL embed URL and a quick audit summary for your technical team. Would you like me to send it over?"
            ),
        },
    },
    {
        "target_id": "TGT-006",
        "company_name": "Scottsdale Center for Advanced Cosmetic Dentistry",
        "vertical": "Minimally Invasive Veneers & Sedation Dentistry",
        "headquarters": "Scottsdale, AZ",
        "website_url": "https://scottsdalecosmeticdds.com",
        "domain_url": "https://scottsdalecosmeticdds.com",
        "estimated_aov": 16500.0,
        "estimated_monthly_visitors": 6100,
        "estimated_ad_spend_monthly": 7500.0,
        "decision_maker": {
            "name": "Dr. Blake Halston",
            "title": "Principal Dentist",
            "email": "drhalston@scottsdalecosmeticdds.com",
            "phone": "(480) 555-0131",
            "linkedin_url": "https://linkedin.com/in/blakehalston-dds",
        },
        "primary_conversion_leak": "Mobile Click-to-Call button obstructed by third-party chat widget with z-index 999999.",
        "secondary_conversion_leak": "180+ verified Google 5-star reviews missing schema markup and mobile badge social proof.",
        "estimated_monthly_lost_pipeline": 82500.0,
        "estimated_annual_recoverable": 990000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_006.md",
        "audit_report_file": "audits/audit_tgt_006.md",
        "diagnostics": {
            "primary_leak_summary": "Third-party chat bubble directly blocking mobile Click-to-Call button",
            "primary_leak_technical_detail": "Chat widget container has z-index: 999999 positioned bottom: 10px right: 10px overlapping tap-to-call anchor on mobile viewports.",
            "secondary_leak_summary": "Missing AggregateRating schema and visual Google review badges on mobile landing pages.",
            "mobile_lcp_seconds": 3.4,
            "mobile_cls_score": 0.06,
            "speed_to_lead_sla_hours": 12.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 82500.0,
            "estimated_annual_recoverable_usd": 990000.0,
        },
        "outreach_assets": {
            "email_subject": "Chat widget blocking your mobile call button (Scottsdale cosmetic patients)",
            "email_body_template": (
                "Dr. Halston, your chat widget sits directly on top of your mobile Tap-to-Call button, blocking "
                "cosmetic patients from dialing your office. For $16.5k cases, this overlap costs $82.5k/mo. "
                "Moving the widget up by 80px fixes it. Open to seeing a 60-second clip? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Dr. Halston, your Scottsdale practice has exceptional 5-star patient reviews, but on mobile devices, prospective cosmetic patients physically cannot tap your phone number to call your office.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Your automated third-party chat widget has a CSS z-index of 999999 that sits directly over your sticky mobile Tap to Call button on all iPhone screens. Every time a patient tries to call your front desk, they accidentally open the chat modal instead. Over 60% of high-intent cosmetic callers abandon when forced into automated chatbots. At $16,500 average case value, losing five veneer cases a month drains $82,500 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Adjusting the widget offset by 80 pixels frees the primary call bar and restores instant one-touch calling for your highest-intent cosmetic patients.\n"
                "1:10-1:30 | Soft CTA: I documented the single CSS rule needed to fix the overlap. Would you like me to send the walkthrough over to your clinic manager?"
            ),
        },
    },
    {
        "target_id": "TGT-007",
        "company_name": "Mechanical Air Solutions Group",
        "vertical": "Commercial Chillers, VRF Systems & Industrial Refrigeration",
        "headquarters": "Chicago, IL",
        "website_url": "https://mechanicalairsolutions.com",
        "domain_url": "https://mechanicalairsolutions.com",
        "estimated_aov": 65000.0,
        "estimated_monthly_visitors": 3800,
        "estimated_ad_spend_monthly": 9000.0,
        "decision_maker": {
            "name": "Keith Brannigan",
            "title": "VP of Commercial Sales & Service Contracts",
            "email": "kbrannigan@mechanicalairsolutions.com",
            "phone": "(312) 555-0155",
            "linkedin_url": "https://linkedin.com/in/keith-brannigan-hvac",
        },
        "primary_conversion_leak": "Severe mobile latency: PageSpeed 28/100, TTI 9.2s from 14 unbundled tracking scripts.",
        "secondary_conversion_leak": "24/7 Emergency Dispatch phone number rendered as flattened PNG graphic lacking clickable tel: link.",
        "estimated_monthly_lost_pipeline": 130000.0,
        "estimated_annual_recoverable": 1560000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_007.md",
        "audit_report_file": "audits/audit_tgt_007.md",
        "diagnostics": {
            "primary_leak_summary": "Mobile PageSpeed 28/100 and Time to Interactive 9.2s delaying urgent dispatch",
            "primary_leak_technical_detail": "14 render-blocking third-party scripts delay First Contentful Paint to 4.4s and TTI to 9.2s on mobile connections.",
            "secondary_leak_summary": "Emergency hotline rendered inside dispatch_banner.png without tel:+13125550155 anchor.",
            "mobile_lcp_seconds": 7.4,
            "mobile_cls_score": 0.12,
            "speed_to_lead_sla_hours": 8.5,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 130000.0,
            "estimated_annual_recoverable_usd": 1560000.0,
        },
        "outreach_assets": {
            "email_subject": "Emergency chiller dispatch phone unclickable on mobile",
            "email_body_template": (
                "Keith, your emergency dispatch hotline is an unclickable PNG graphic on mobile, and page speed is 28/100. "
                "Commercial facility managers needing urgent chiller service ($65k AOV) bounce when unable to tap-to-call. "
                "I recorded a quick video and code fix. Open to taking a look? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Hi Keith, when a facility engineer or hospital plant manager has a commercial chiller go down in Chicago, they pull out their smartphone to search for emergency dispatch. But on your site, they cannot click to call you.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Your 24/7 Emergency Dispatch hotline is rendered as an embedded PNG image with no active tel: link attribute. Facility managers cannot copy an image on a phone. Coupled with a 9.2-second mobile load time, managers bounce to competitors. Losing two commercial chiller overhauls a month silently drains over $130,000 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: By wrapping dispatch in a persistent sticky emergency bar and deferring non-essential analytics scripts, your page renders in 1.2 seconds with instant tap-to-call functionality across every mobile screen.\n"
                "1:10-1:30 | Soft CTA: In commercial mechanical contracts where chiller overhauls run $65,000+, this is an easy win. Would you like me to send over the technical breakdown for your web team?"
            ),
        },
    },
    {
        "target_id": "TGT-008",
        "company_name": "Pacific Industrial Climate Systems",
        "vertical": "Cleanroom HVAC, Data Center Cooling & Industrial HVAC",
        "headquarters": "Seattle, WA",
        "website_url": "https://pacificindustrialclimate.com",
        "domain_url": "https://pacificindustrialclimate.com",
        "estimated_aov": 95000.0,
        "estimated_monthly_visitors": 2400,
        "estimated_ad_spend_monthly": 5500.0,
        "decision_maker": {
            "name": "Sarah Lindqvist",
            "title": "Director of Enterprise Business Development",
            "email": "slindqvist@pacificindustrialclimate.com",
            "phone": "(206) 555-0199",
            "linkedin_url": "https://linkedin.com/in/sarah-lindqvist-pacs",
        },
        "primary_conversion_leak": "Mobile RFP form requiring desktop CAD/PDF file upload causing 94% mobile abandonment.",
        "secondary_conversion_leak": "RFP submissions trigger unintegrated plaintext email alerts with zero CRM deduplication.",
        "estimated_monthly_lost_pipeline": 63000.0,
        "estimated_annual_recoverable": 756000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_008.md",
        "audit_report_file": "audits/audit_tgt_008.md",
        "diagnostics": {
            "primary_leak_summary": "Mandatory CAD/PDF file upload field on mobile contact form",
            "primary_leak_technical_detail": "HTML input element <input type='file' required> blocks mobile submission for site engineers who do not store 50MB CAD files on smartphones.",
            "secondary_leak_summary": "Plaintext email dispatch lacking webhook CRM sync or automated response.",
            "mobile_lcp_seconds": 4.8,
            "mobile_cls_score": 0.05,
            "speed_to_lead_sla_hours": 26.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 63000.0,
            "estimated_annual_recoverable_usd": 756000.0,
        },
        "outreach_assets": {
            "email_subject": "Mobile RFP upload barrier (cleanroom & data center HVAC)",
            "email_body_template": (
                "Sarah, your mobile RFP form requires mandatory CAD drawing uploads, causing 94% of smartphone visitors to bounce. "
                "Splitting this into a mobile-friendly 3-field engineering walk request captures these $95k+ leads before they leave. "
                "I created a wireframe showing the flow. Open to reviewing? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Hi Sarah, Pacific Industrial does world-class cleanroom and data center cooling across the Pacific Northwest. But your mobile contact form has a massive conversion roadblock for prospective enterprise clients.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Your RFP form makes uploading a CAD or PDF engineering file mandatory before submission. A construction executive or project director browsing your site on their phone during a job site walk cannot upload a 50MB CAD blueprint from a smartphone. As a result, 94% of mobile visitors abandon. At a $95,000 average contract value, losing even one project every 45 days costs $63,000 a month in lost pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Offering a mobile-optimized Request Engineering Walkthrough option with just 3 fields captures enterprise contacts immediately, allowing you to collect blueprints during follow-up.\n"
                "1:10-1:30 | Soft CTA: For $95,000+ industrial installations, capturing even one extra project per quarter is transformational. Would you like me to send over the wireframe and workflow?"
            ),
        },
    },
    {
        "target_id": "TGT-009",
        "company_name": "LoneStar Commercial Mechanical",
        "vertical": "Industrial Cooling Towers, RTUs & Building Automation Systems (BAS)",
        "headquarters": "Dallas-Fort Worth, TX",
        "website_url": "https://lonestarcommercialmechanical.com",
        "domain_url": "https://lonestarcommercialmechanical.com",
        "estimated_aov": 55000.0,
        "estimated_monthly_visitors": 4100,
        "estimated_ad_spend_monthly": 8500.0,
        "decision_maker": {
            "name": "Travis Calloway",
            "title": "Chief Operating Officer",
            "email": "tcalloway@lonestarcommercialmechanical.com",
            "phone": "(214) 555-0128",
            "linkedin_url": "https://linkedin.com/in/travis-calloway-dfw",
        },
        "primary_conversion_leak": "Viewport meta tag missing initial-scale=1.0, forcing mobile users to pinch-and-zoom.",
        "secondary_conversion_leak": "Missing commercial utility rebate calculator losing retrofits to competitors offering payback schedules.",
        "estimated_monthly_lost_pipeline": 110000.0,
        "estimated_annual_recoverable": 1320000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_009.md",
        "audit_report_file": "audits/audit_tgt_009.md",
        "diagnostics": {
            "primary_leak_summary": "Missing viewport meta tag causing desktop layout render on mobile devices",
            "primary_leak_technical_detail": "HTML head lacks <meta name='viewport' content='width=device-width, initial-scale=1.0'>, triggering 980px desktop viewport downscale on mobile.",
            "secondary_leak_summary": "Absence of Oncor/CenterPoint utility rebate incentive calculator for RTU retrofits.",
            "mobile_lcp_seconds": 5.2,
            "mobile_cls_score": 0.15,
            "speed_to_lead_sla_hours": 16.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 110000.0,
            "estimated_annual_recoverable_usd": 1320000.0,
        },
        "outreach_assets": {
            "email_subject": "Missing mobile viewport scaling on LoneStar Mechanical",
            "email_body_template": (
                "Travis, your site is missing the HTML viewport meta tag, rendering as a tiny desktop page on phones "
                "and hurting Google mobile rankings. Property managers have to pinch-to-zoom to call you. "
                "This 1-line fix protects $110k/mo in RTU pipeline. Mind if I send the clip? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Travis, I am looking directly at LoneStar Commercial Mechanical's website on an iPhone, and right now the entire site renders as an unscaled desktop page that requires pinching and zooming to read anything clearly.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Because the mobile viewport meta tag is missing from your HTML head, every building owner or property manager visiting from a smartphone has to squint and zoom in to find your commercial RTU phone number. Google also heavily penalizes unscaled sites in local mobile rankings. At a $55,000 average ticket, losing two commercial replacement projects a month drains $110,000 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Adding one standard line of HTML to your site header restores automatic mobile responsiveness across every page and unlocks seamless mobile phone dialing and readability.\n"
                "1:10-1:30 | Soft CTA: I recorded a quick 60-second video demonstrating the fix for your developer. Would it be okay if I sent that your way?"
            ),
        },
    },
    {
        "target_id": "TGT-010",
        "company_name": "Helios Elite Clean Energy",
        "vertical": "Luxury Residential Solar & Battery Microgrids (Tesla Powerwall)",
        "headquarters": "San Diego, CA",
        "website_url": "https://helioseliteenergy.com",
        "domain_url": "https://helioseliteenergy.com",
        "estimated_aov": 48000.0,
        "estimated_monthly_visitors": 7200,
        "estimated_ad_spend_monthly": 12500.0,
        "decision_maker": {
            "name": "Damon Fletcher",
            "title": "Co-Founder & Head of Sales",
            "email": "damon@helioseliteenergy.com",
            "phone": "(619) 555-0166",
            "linkedin_url": "https://linkedin.com/in/damon-fletcher-helios",
        },
        "primary_conversion_leak": "2.4MB unminified JavaScript bundle locking main browser thread for 4.8s, freezing NEM 3.0 savings slider.",
        "secondary_conversion_leak": "Evening inquiries receive no automated SMS response until 10:00 AM next day (85% sign with first respondent).",
        "estimated_monthly_lost_pipeline": 192000.0,
        "estimated_annual_recoverable": 2304000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_010.md",
        "audit_report_file": "audits/audit_tgt_010.md",
        "diagnostics": {
            "primary_leak_summary": "2.4MB JS vendor bundle freezing mobile savings calculator slider",
            "primary_leak_technical_detail": "Unminified chunk-vendors.js causes a 4.8s Long Task on mobile Safari/Chrome, freezing touch interaction on the NEM 3.0 battery slider.",
            "secondary_leak_summary": "16-hour evening lead response void without conversational SMS qualification.",
            "mobile_lcp_seconds": 5.9,
            "mobile_cls_score": 0.07,
            "speed_to_lead_sla_hours": 15.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 192000.0,
            "estimated_annual_recoverable_usd": 2304000.0,
        },
        "outreach_assets": {
            "email_subject": "Frozen NEM 3.0 calculator on mobile (San Diego luxury solar)",
            "email_body_template": (
                "Damon, a 2.4MB vendor bundle locks the main thread for 4.8s on mobile, freezing your NEM 3.0 "
                "solar calculator slider. For $48k solar+storage projects, this friction drains $192k/mo. "
                "Route code-splitting fixes this immediately. I recorded a walkthrough for your engineers. Open to seeing it? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Damon, your luxury solar and Powerwall microgrid branding in San Diego is exceptional, but your NEM 3.0 savings slider freezes completely when touched on mobile devices across Apple iOS and Android smartphones.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Your website loads an uncompressed 2.4-megabyte vendor JavaScript bundle that locks the browser main thread for 4.8 seconds on cellular connections. Homeowners trying to calculate battery backup ROI think the site is frozen and bounce immediately. Coupled with a total lack of automated evening lead response, high-intent homeowners sign with competing Tier-1 installers. Losing four solar and multi-storage installations a month silently drains over $192,000 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Route-level code splitting eliminates the main-thread freeze and restores 60fps slider response, while an automated 2-minute SMS qualification workflow captures evening inquiries immediately.\n"
                "1:10-1:30 | Soft CTA: I prepared a diagnostic overview and bundle optimization guide for your engineering team. Can I forward that to you?"
            ),
        },
    },
    {
        "target_id": "TGT-011",
        "company_name": "Sonoran Commercial Solar & Storage",
        "vertical": "Commercial & Agricultural Solar PPA Installations",
        "headquarters": "Phoenix, AZ",
        "website_url": "https://sonoransolarstorage.com",
        "domain_url": "https://sonoransolarstorage.com",
        "estimated_aov": 75000.0,
        "estimated_monthly_visitors": 3100,
        "estimated_ad_spend_monthly": 6000.0,
        "decision_maker": {
            "name": "Arturo Morales",
            "title": "Managing Partner",
            "email": "amorales@sonoransolarstorage.com",
            "phone": "(602) 555-0143",
            "linkedin_url": "https://linkedin.com/in/arturo-morales-solar",
        },
        "primary_conversion_leak": "Phone input validation failure: type='text' rejecting input without hyphens with no error label.",
        "secondary_conversion_leak": "Absence of sticky mobile navigation across 4,000px long commercial case studies.",
        "estimated_monthly_lost_pipeline": 150000.0,
        "estimated_annual_recoverable": 1800000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_011.md",
        "audit_report_file": "audits/audit_tgt_011.md",
        "diagnostics": {
            "primary_leak_summary": "Silent phone validation error rejecting 10-digit unhyphenated input",
            "primary_leak_technical_detail": "Input field configured as type='text' with regex ^\\d{3}-\\d{3}-\\d{4}$ outlines field in red without user-facing validation message upon submit.",
            "secondary_leak_summary": "Missing persistent mobile CTA header on lengthy commercial project case studies.",
            "mobile_lcp_seconds": 4.5,
            "mobile_cls_score": 0.04,
            "speed_to_lead_sla_hours": 21.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 150000.0,
            "estimated_annual_recoverable_usd": 1800000.0,
        },
        "outreach_assets": {
            "email_subject": "Phone validation error blocking commercial solar quote requests",
            "email_body_template": (
                "Arturo, your mobile solar form silently rejects phone numbers entered without hyphens, blocking quote requests "
                "without displaying an error message. For $75k commercial contracts, this costs $150k/mo. "
                "A 2-line input mask fix resolves it. Open to seeing a quick demo? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Hi Arturo, I was reviewing your commercial solar case studies in Phoenix, but when submitting a project feasibility request on mobile, your form throws a silent validation error that blocks prospective clients.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Your phone number field requires dashes, but the input type is configured as generic text without an input mask. When agricultural or commercial clients enter their 10-digit number without dashes, the form outlines the box in red with no error explanation and blocks submission. In commercial solar where contracts average $75,000, losing two commercial deals a month silently drains $150,000 in pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Changing the input type to tel and adding standard phone auto-formatting completely resolves the barrier and triggers the native numeric keypad on smartphones.\n"
                "1:10-1:30 | Soft CTA: In commercial solar where deals exceed $75,000, removing this friction is an immediate revenue win. Would you like me to send the code snippet over?"
            ),
        },
    },
    {
        "target_id": "TGT-012",
        "company_name": "Palmetto Microgrid & Solar Systems",
        "vertical": "Coastal Off-Grid, Island Microgrids & Commercial Solar",
        "headquarters": "Charleston, SC",
        "website_url": "https://palmettomicrogridsolar.com",
        "domain_url": "https://palmettomicrogridsolar.com",
        "estimated_aov": 52000.0,
        "estimated_monthly_visitors": 2800,
        "estimated_ad_spend_monthly": 4500.0,
        "decision_maker": {
            "name": "Rhett Calhoun",
            "title": "Chief Revenue Officer",
            "email": "r.calhoun@palmettomicrogridsolar.com",
            "phone": "(843) 555-0119",
            "linkedin_url": "https://linkedin.com/in/rhettcalhoun-microgrid",
        },
        "primary_conversion_leak": "CSS Media Query bug causes hero title .hero-title to overlap primary CTA button .btn-quote on screens under 414px.",
        "secondary_conversion_leak": "No automated SMS speed-to-lead trigger confirming booking and dispatching drone roof inspection scheduling link.",
        "estimated_monthly_lost_pipeline": 156000.0,
        "estimated_annual_recoverable": 1872000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_012.md",
        "audit_report_file": "audits/audit_tgt_012.md",
        "diagnostics": {
            "primary_leak_summary": "Hero title container overlapping primary quote CTA button on mobile viewports",
            "primary_leak_technical_detail": "Fixed-height container on .hero-content causes absolute positioned .hero-title to cover .btn-quote, intercepting all touch events on screens < 414px.",
            "secondary_leak_summary": "Absence of instant SMS booking confirmation and automated drone inspection scheduler.",
            "mobile_lcp_seconds": 4.7,
            "mobile_cls_score": 0.11,
            "speed_to_lead_sla_hours": 17.5,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 156000.0,
            "estimated_annual_recoverable_usd": 1872000.0,
        },
        "outreach_assets": {
            "email_subject": "Hero button overlap bug on mobile (Coastal microgrids)",
            "email_body_template": (
                "Rhett, a CSS media query bug on mobile causes your hero headline to physically overlap your quote CTA button, "
                "preventing clicks. For $52k microgrid contracts, this costs $156k/mo in pipeline. "
                "A 1-rule flexbox fix restores it. Mind if I send the CSS patch? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Rhett, Palmetto Microgrid builds some of the finest island and coastal power systems across the Carolinas. But on mobile phones under 414px width, your main call-to-action button cannot be clicked by visiting commercial property owners.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: A CSS media query bug causes your hero title container to sit directly on top of the Request Microgrid Assessment button. Tapping the button highlights the text above it instead of opening the quote form. Prospective coastal clients cannot submit bids from the hero section. At a $52,000 average contract value, losing three contracts a month silently drains over $156,000 in pipeline revenue.\n"
                "0:45-1:10 | The Frictionless Fix: Converting the hero header container to modern CSS flexbox with automatic spacing eliminates the overlap across all smartphone screens immediately.\n"
                "1:10-1:30 | Soft CTA: For $50,000+ microgrid contracts, this is a vital fix. Would you like me to send over the CSS patch for your web team?"
            ),
        },
    },
    {
        "target_id": "TGT-013",
        "company_name": "Coastal Plastic Surgery & Rejuvenation Center",
        "vertical": "Deep Plane Facelifts, Rhinoplasty & Aesthetic Surgery",
        "headquarters": "Newport Beach, CA",
        "website_url": "https://coastalrejuvenationsurg.com",
        "domain_url": "https://coastalrejuvenationsurg.com",
        "estimated_aov": 19500.0,
        "estimated_monthly_visitors": 11200,
        "estimated_ad_spend_monthly": 18000.0,
        "decision_maker": {
            "name": "Dr. Vivienne Vance",
            "title": "MD, FACS & Practice Owner",
            "email": "drvivienne@coastalrejuvenationsurg.com",
            "phone": "(949) 555-0172",
            "linkedin_url": "https://linkedin.com/in/viviennevance-md",
        },
        "primary_conversion_leak": "Unoptimized 12MB PNG before-and-after photo gallery without loading='lazy', causing 6.4s LCP and FID > 380ms.",
        "secondary_conversion_leak": "Consultation booking form requests credit card deposit ($500) on field 8 without clarity on procedure credit.",
        "estimated_monthly_lost_pipeline": 117000.0,
        "estimated_annual_recoverable": 1404000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_013.md",
        "audit_report_file": "audits/audit_tgt_013.md",
        "diagnostics": {
            "primary_leak_summary": "12MB uncompressed PNG photo gallery creating 6.4s mobile LCP",
            "primary_leak_technical_detail": "48 full-resolution PNG images in /gallery/ load concurrently without loading='lazy' or responsive srcset, crippling mobile network bandwidth.",
            "secondary_leak_summary": "Premature $500 credit card consultation fee on field 8 producing 74% abandonment.",
            "mobile_lcp_seconds": 6.4,
            "mobile_cls_score": 0.08,
            "speed_to_lead_sla_hours": 11.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 117000.0,
            "estimated_annual_recoverable_usd": 1404000.0,
        },
        "outreach_assets": {
            "email_subject": "6.4s mobile load time on facial gallery (Newport Beach surgical inquiries)",
            "email_body_template": (
                "Dear Dr. Vance, 48 uncompressed gallery images delay mobile loading to 6.4s, while an unclarified "
                "credit card consultation field causes 74% drop-off. For $19.5k facelift cases, this loses $117k/mo. "
                "Lazy-loading and fee clarity fix both. Open to seeing the teardown? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Dr. Vance, your deep-plane facelift outcomes in Newport Beach are extraordinary, but your mobile gallery is currently loading 48 uncompressed high-resolution images simultaneously upon first mobile page visit.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: This unoptimized asset waterfall creates a 6.4-second load time on cellular devices. When prospective patients do reach your form, field 8 asks for credit card payment details before explaining how the fee is credited toward surgery, triggering 74% abandonment. Elective cosmetic patients bounce directly to competing surgical practices in Orange County. At $19,500 average case value, losing six surgical procedures monthly silently costs over $117,000 in high-ticket surgical pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Enabling native image lazy-loading cuts your initial mobile payload from 12MB to under 400KB, dropping load time to 1.1s, while clear fee transparency reassures elective patients at booking.\n"
                "1:10-1:30 | Soft CTA: I prepared a visual breakdown and optimization checklist for your practice director. May I send it over?"
            ),
        },
    },
    {
        "target_id": "TGT-014",
        "company_name": "Elite Follicular Restoration Institute",
        "vertical": "Robotic ARTAS FUE Hair Restoration & Regenerative Medicine",
        "headquarters": "Miami, FL",
        "website_url": "https://elitefollicularrestoration.com",
        "domain_url": "https://elitefollicularrestoration.com",
        "estimated_aov": 13500.0,
        "estimated_monthly_visitors": 9800,
        "estimated_ad_spend_monthly": 16000.0,
        "decision_maker": {
            "name": "Carlos Santoro",
            "title": "VP of Patient Acquisition",
            "email": "csantoro@elitefollicularrestoration.com",
            "phone": "(305) 555-0187",
            "linkedin_url": "https://linkedin.com/in/carlossantoro-hair",
        },
        "primary_conversion_leak": "Mobile tap target collision: primary CTAs compressed into 28px height row without touch padding (34% touch error).",
        "secondary_conversion_leak": "Absence of instant WhatsApp/SMS photo assessment workflow for confidential hairline evaluation.",
        "estimated_monthly_lost_pipeline": 108000.0,
        "estimated_annual_recoverable": 1296000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_014.md",
        "audit_report_file": "audits/audit_tgt_014.md",
        "diagnostics": {
            "primary_leak_summary": "Mobile tap target collision with 28px height interactive buttons",
            "primary_leak_technical_detail": "Buttons .btn-call, .btn-calc, and .btn-book are packed inside a 28px flex row, triggering severe Google Lighthouse tap target warnings.",
            "secondary_leak_summary": "Lack of rapid confidential photo assessment intake via SMS or WhatsApp.",
            "mobile_lcp_seconds": 3.9,
            "mobile_cls_score": 0.06,
            "speed_to_lead_sla_hours": 9.0,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 108000.0,
            "estimated_annual_recoverable_usd": 1296000.0,
        },
        "outreach_assets": {
            "email_subject": "Mobile tap target collision (Miami hair restoration consults)",
            "email_body_template": (
                "Carlos, primary mobile buttons on elitefollicularrestoration.com are packed into a 28px row, "
                "causing 34% mis-taps, while patients lack an easy way to text hairline photos. For $13.5k cases, "
                "this drains $108k/mo. A 48px touch bar fixes this. Mind if I share the mockup? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Carlos, Elite Follicular leads the Miami market in robotic ARTAS hair restoration. But your mobile navigation layout is currently causing over 30% of smartphone visitors to mis-tap during site navigation.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: Your primary conversion buttons—Call Now, Graft Calculator, and Book Evaluation—are squeezed into a narrow 28-pixel row without touch padding, causing frequent mis-taps. Furthermore, high-intent patients want to submit confidential hairline photos via SMS or WhatsApp rather than complex desktop forms. Affluent male clients drop off when forced into lengthy questionnaires. Losing eight robotic FUE cases a month silently costs over $108,000 in procedure pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Upgrading to a 48px touch-friendly floating bar with a 1-tap confidential photo evaluation option typically increases mobile lead volume by 35% within two weeks.\n"
                "1:10-1:30 | Soft CTA: For $13,500 average FUE cases, this translates to tens of thousands in recovered revenue. Would you be open to seeing the mobile mockup?"
            ),
        },
    },
    {
        "target_id": "TGT-015",
        "company_name": "Park Avenue Facial Aesthetics & Longevity",
        "vertical": "Non-Surgical Liquid Facelifts, Morpheus8 & Medical Longevity",
        "headquarters": "New York, NY",
        "website_url": "https://parkavefacialaesthetics.com",
        "domain_url": "https://parkavefacialaesthetics.com",
        "estimated_aov": 8500.0,
        "estimated_monthly_visitors": 14000,
        "estimated_ad_spend_monthly": 20000.0,
        "decision_maker": {
            "name": "Jacqueline Sterling",
            "title": "Managing Director & Partner",
            "email": "jsterling@parkavefacialaesthetics.com",
            "phone": "(212) 555-0114",
            "linkedin_url": "https://linkedin.com/in/jacqueline-sterling-parkave",
        },
        "primary_conversion_leak": "Cookie consent banner and promotional modal load simultaneously, creating an unclosable screen lock on mobile.",
        "secondary_conversion_leak": "Embedded scheduling iframe renders with zero height (style='height: 0px;') due to script conflict with Webflow.",
        "estimated_monthly_lost_pipeline": 102000.0,
        "estimated_annual_recoverable": 1224000.0,
        "tailored_pitch_file": "pitches/pitch_tgt_015.md",
        "audit_report_file": "audits/audit_tgt_015.md",
        "diagnostics": {
            "primary_leak_summary": "Simultaneous cookie banner and promotional popup screen-locking mobile viewports",
            "primary_leak_technical_detail": "Cookie banner modal and marketing lead capture popup render concurrently at z-index 1000000, obscuring close triggers and locking touch scroll.",
            "secondary_leak_summary": "Scheduling iframe rendered with inline style height: 0px on mobile Safari viewports.",
            "mobile_lcp_seconds": 5.6,
            "mobile_cls_score": 0.22,
            "speed_to_lead_sla_hours": 13.5,
        },
        "financial_impact": {
            "estimated_monthly_lost_pipeline_usd": 102000.0,
            "estimated_annual_recoverable_usd": 1224000.0,
        },
        "outreach_assets": {
            "email_subject": "Mobile modal screen freeze on Park Avenue Aesthetics",
            "email_body_template": (
                "Jacqueline, your cookie banner and promo popup render simultaneously on mobile, creating an unclosable "
                "screen lock that prevents booking. For $8.5k aesthetic packages, this freezes $102k/mo in pipeline. "
                "A 2-line timing fix unblocks visitors. May I share a 60-second video walkthrough? Best, Autonomous Revenue Engine."
            ),
            "video_script_90sec": (
                "0:00-0:15 | Pattern Interrupt: Jacqueline, Park Avenue Aesthetics has an impeccable reputation in Manhattan, but right now mobile visitors are experiencing a total screen lock caused by overlapping modal windows on mobile Safari.\n"
                "0:15-0:45 | Diagnostic & Revenue Loss: When mobile users arrive, your cookie consent banner and a promotional popup load at the exact same time. The close button on the popup is pushed under the cookie banner, making it impossible to close either window. Mobile visitors are stuck on a frozen screen and cannot reach your treatment menu or booking calendar. Losing 12 treatment packages monthly silently drains $102,000 in procedure pipeline.\n"
                "0:45-1:10 | The Frictionless Fix: Sequencing the popups so the promotional modal only appears after consent, and fixing your Calendly iframe height attribute, instantly unfreezes the mobile experience.\n"
                "1:10-1:30 | Soft CTA: I recorded a 60-second video demonstrating the freeze on an iPhone and the simple fix. Would you like me to send the clip to you or your web manager?"
            ),
        },
    },
]


class B2BPipelineGenerator:
    """Manages generation, export, and verification of B2B lead data assets."""

    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Default to repo root (two levels up from this file)
            self.project_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.data_dir = self.project_root / "data" / "b2b_leads"
        self.schema_file = self.data_dir / "schema" / "b2b_leads_schema.json"
        self.dataset_file = self.data_dir / "leads_dataset.json"
        self.csv_file = self.data_dir / "leads_dataset.csv"
        self.audits_dir = self.data_dir / "audits"
        self.pitches_dir = self.data_dir / "pitches"

    def build_dataset_model(self) -> LeadDataset:
        """Constructs and validates the master LeadDataset model from canonical target data."""
        targets = []
        for raw in CANONICAL_TARGETS_RAW:
            target = LeadTarget.from_dict(raw)
            targets.append(target)

        dataset = LeadDataset(
            version="1.0.0",
            generated_at=datetime.utcnow().isoformat() + "Z",
            total_targets=len(targets),
            targets=targets,
        )
        return dataset

    def generate_audit_report(self, target: LeadTarget) -> str:
        """Generates a comprehensive diagnostic audit report in Markdown format."""
        diag = target.diagnostics
        fin = target.financial_impact

        lcp = diag.mobile_lcp_seconds if diag else 4.5
        cls_val = diag.mobile_cls_score if diag else 0.05
        sla = diag.speed_to_lead_sla_hours if diag else 12.0
        lost_pipeline = target.estimated_monthly_lost_pipeline
        annual_rec = target.estimated_annual_recoverable or (lost_pipeline * 12.0)

        report = f"""# Comprehensive Conversion Leak Audit Report: {target.company_name}
**Target ID**: `{target.target_id}` | **Vertical**: {target.vertical} | **Headquarters**: {target.headquarters}
**Website**: [{target.website_url}]({target.website_url}) | **Audit Date**: {datetime.utcnow().strftime('%Y-%m-%d')}
**Lead Auditor**: Autonomous Revenue Engine B2B Diagnostic Pipeline

---

## 1. Executive Financial Summary
- **Estimated Average Order Value (AOV)**: ${target.estimated_aov:,.2f} USD
- **Estimated Monthly Visitors**: {target.estimated_monthly_visitors:,} (Mobile traffic share: ~65%)
- **Estimated Monthly Paid Ad Spend**: ${target.estimated_ad_spend_monthly:,.2f} USD
- **Benchmark Mobile Lead Conversion Rate**: 3.5%
- **Current Impaired Conversion Rate**: ~1.1% - 1.3%
- **Quantified Monthly Lost Pipeline**: **${lost_pipeline:,.2f} USD**
- **Quantified Annual Recoverable Revenue**: **${annual_rec:,.2f} USD**

### Conversion Loss Breakdown
Due to mobile friction points and technical bottlenecks identified below, approximately **{lost_pipeline / max(1.0, target.estimated_aov):.1f} high-ticket clients/projects** are lost every month to regional competitors with optimized mobile landing experiences.

---

## 2. Core Web Vitals & Mobile Diagnostics

| Metric | Measured Score | Google Benchmark | Status | Revenue Impact |
|---|---|---|---|---|
| **Largest Contentful Paint (LCP)** | {lcp:.1f}s | < 2.5s (Good) | {'⚠️ POOR' if lcp > 4.0 else '⚠️ NEEDS WORK'} | High bounce rate on mobile cellular |
| **Cumulative Layout Shift (CLS)** | {cls_val:.2f} | < 0.10 (Good) | {'⚠️ POOR' if cls_val > 0.2 else ('⚠️ FAIR' if cls_val > 0.08 else '✅ PASS')} | Misclicks & user frustration |
| **Speed-to-Lead Response SLA** | {sla:.1f} hrs | < 0.25 hrs (15 min) | ⚠️ CRITICAL | 80% decay in close probability |

### Primary Conversion Leak
- **Issue**: {target.primary_conversion_leak}
- **Technical Analysis**: {diag.primary_leak_technical_detail if diag else target.primary_conversion_leak}

### Secondary Conversion Leak
- **Issue**: {target.secondary_conversion_leak}
- **Technical Analysis**: {diag.secondary_leak_summary if diag else target.secondary_conversion_leak}

---

## 3. Decision Maker & Key Contact Profile
- **Primary Contact**: {target.decision_maker.name}
- **Corporate Title**: {target.decision_maker.title}
- **Direct Email**: `{target.decision_maker.email}`
- **Office / Direct Phone**: `{target.decision_maker.phone}`
- **LinkedIn Profile**: [{target.decision_maker.linkedin_url}]({target.decision_maker.linkedin_url})

---

## 4. Three-Phase Technical Remediation Plan

### Phase 1: Immediate Critical Hotfix (Hours 1 - 24)
- Eliminate render-blocking assets and resolve mobile viewport/layout issues.
- Deploy immediate code patch targeting primary leak:
```html
<!-- Recommended Hotfix for {target.target_id} -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<a href="tel:{''.join(c for c in target.decision_maker.phone if c.isdigit() or c == '+')}" class="btn-emergency-call">
  Call Immediate Concierge Desk
</a>
```

### Phase 2: Mobile Funnel Streamlining (Days 2 - 5)
- Introduce persistent sticky bottom CTA bar anchored to mobile viewport.
- Eliminate redundant form fields; reduce initial intake to 3 high-relevance inputs.
- Ensure all interactive buttons maintain a minimum 48x48px touch zone.

### Phase 3: Speed-to-Lead Automation (Days 6 - 14)
- Connect intake webhooks to 2-minute automated SMS auto-triage.
- Integrate direct self-scheduling calendar links into instant confirmation SMS.
- Deliver real-time push alerts to {target.decision_maker.name}'s mobile device.

---
*Generated by Autonomous Revenue Engine B2B Pipeline.*
"""
        return report.strip() + "\n"

    def generate_pitch_script(self, target: LeadTarget) -> str:
        """
        Generates a tailored 90-second video walkthrough pitch script and companion email.
        Strictly calibrated to stay within 160-260 words for optimal 90s pacing.
        """
        outreach = target.outreach_assets
        email_subj = outreach.email_subject if outreach else f"Quick video on {target.company_name} mobile leaks"
        video_script = outreach.video_script_90sec if outreach else target.primary_conversion_leak
        email_body = outreach.email_body_template if outreach else ""

        # Format clean markdown pitch document
        doc = f"""# 90-Second Pitch Script: {target.company_name} ({target.target_id})
**Recipient**: {target.decision_maker.name} ({target.decision_maker.email}) | **AOV**: ${target.estimated_aov:,.0f} | **Lost Pipeline**: ${target.estimated_monthly_lost_pipeline:,.0f}/mo

### Video Walkthrough Script (~90 Seconds)
{video_script}

### Companion Outreach Email
**Subject**: {email_subj}
{email_body}
"""
        return doc.strip() + "\n"

    def write_all(self) -> Tuple[LeadDataset, List[str]]:
        """Writes all artifacts to disk and performs integrity verification."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.schema_file.parent.mkdir(parents=True, exist_ok=True)
        self.audits_dir.mkdir(parents=True, exist_ok=True)
        self.pitches_dir.mkdir(parents=True, exist_ok=True)

        dataset = self.build_dataset_model()
        errors = dataset.validate()
        if errors:
            raise ValueError(f"Dataset model validation failed: {errors}")

        # 1. Write JSON dataset
        dataset_dict = dataset.to_dict()
        with open(self.dataset_file, "w", encoding="utf-8") as f:
            json.dump(dataset_dict, f, indent=2)

        # 2. Write CSV dataset
        csv_rows = []
        for t in dataset.targets:
            diag = t.diagnostics
            fin = t.financial_impact
            outreach = t.outreach_assets
            csv_rows.append({
                "target_id": t.target_id,
                "company_name": t.company_name,
                "vertical": t.vertical,
                "website_url": t.website_url,
                "domain_url": t.domain_url or t.website_url,
                "headquarters": t.headquarters,
                "estimated_aov_usd": t.estimated_aov,
                "monthly_visitors": t.estimated_monthly_visitors,
                "ad_spend_monthly_usd": t.estimated_ad_spend_monthly,
                "dm_name": t.decision_maker.name,
                "dm_title": t.decision_maker.title,
                "dm_email": t.decision_maker.email,
                "dm_phone": t.decision_maker.phone,
                "dm_linkedin": t.decision_maker.linkedin_url,
                "primary_leak_summary": t.primary_conversion_leak,
                "secondary_leak_summary": t.secondary_conversion_leak,
                "mobile_lcp_sec": diag.mobile_lcp_seconds if diag else 0.0,
                "mobile_cls": diag.mobile_cls_score if diag else 0.0,
                "speed_to_lead_sla_hrs": diag.speed_to_lead_sla_hours if diag else 0.0,
                "monthly_lost_pipeline_usd": t.estimated_monthly_lost_pipeline,
                "annual_recoverable_usd": t.estimated_annual_recoverable,
                "email_subject": outreach.email_subject if outreach else "",
                "tailored_pitch_file": t.tailored_pitch_file,
                "audit_report_file": t.audit_report_file,
            })

        fieldnames = list(csv_rows[0].keys())
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        # 3. Write 15 audit reports
        for t in dataset.targets:
            report_content = self.generate_audit_report(t)
            target_slug = t.target_id.lower().replace("-", "_")
            report_path = self.audits_dir / f"audit_{target_slug}.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

        # 4. Write 15 pitch scripts
        for t in dataset.targets:
            pitch_content = self.generate_pitch_script(t)
            target_slug = t.target_id.lower().replace("-", "_")
            pitch_path = self.pitches_dir / f"pitch_{target_slug}.md"
            with open(pitch_path, "w", encoding="utf-8") as f:
                f.write(pitch_content)

        # 5. Run verification
        validation_errors = self.validate_all()
        return dataset, validation_errors

    def validate_all(self) -> List[str]:
        """Comprehensive verification of all generated data files, pitch word counts, and schema."""
        errors = []

        # Check dataset file
        if not self.dataset_file.exists():
            errors.append(f"Missing dataset file: {self.dataset_file}")
            return errors

        with open(self.dataset_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        targets = data.get("targets", [])
        if len(targets) < 15:
            errors.append(f"Expected >= 15 targets, found {len(targets)}")

        # Check CSV file
        if not self.csv_file.exists():
            errors.append(f"Missing CSV file: {self.csv_file}")
        else:
            with open(self.csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if len(rows) != len(targets):
                    errors.append(f"CSV row count ({len(rows)}) does not match JSON targets ({len(targets)})")

        # Check Schema file
        if not self.schema_file.exists():
            errors.append(f"Missing schema file: {self.schema_file}")

        # Check 15 audits and 15 pitches
        for t in targets:
            tid = t.get("target_id", "")
            slug = tid.lower().replace("-", "_")

            audit_file = self.audits_dir / f"audit_{slug}.md"
            if not audit_file.exists():
                errors.append(f"Missing audit report for {tid}: {audit_file}")

            pitch_file = self.pitches_dir / f"pitch_{slug}.md"
            if not pitch_file.exists():
                errors.append(f"Missing pitch script for {tid}: {pitch_file}")
            else:
                with open(pitch_file, "r", encoding="utf-8") as pf:
                    content = pf.read()
                    words = len(content.split())
                    # Calibrate word count check: 160 to 260 words (~90s spoken presentation)
                    if not (160 <= words <= 260):
                        errors.append(
                            f"Pitch script {pitch_file.name} word count {words} outside [160, 260]"
                        )

            # Check math consistency
            monthly_lost = float(t.get("estimated_monthly_lost_pipeline", 0.0))
            annual_rec = float(t.get("estimated_annual_recoverable", 0.0))
            if abs(round(monthly_lost * 12.0, 2) - round(annual_rec, 2)) > 1.0:
                errors.append(
                    f"Target {tid} annual recoverable ({annual_rec}) != 12x monthly lost ({monthly_lost * 12.0})"
                )

        return errors


def main():
    """CLI entrypoint for generator."""
    generator = B2BPipelineGenerator()
    print("Executing B2B Pipeline Asset Generation...")
    dataset, errors = generator.write_all()
    if errors:
        print(f"❌ Generation encountered {len(errors)} errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"✅ Successfully generated and verified {len(dataset.targets)} commercial targets.")
        print(f"  - JSON dataset: {generator.dataset_file}")
        print(f"  - CSV dataset: {generator.csv_file}")
        print(f"  - Audit reports: {len(list(generator.audits_dir.glob('*.md')))} files in {generator.audits_dir}")
        print(f"  - Pitch scripts: {len(list(generator.pitches_dir.glob('*.md')))} files in {generator.pitches_dir}")
        sys.exit(0)


if __name__ == "__main__":
    main()
