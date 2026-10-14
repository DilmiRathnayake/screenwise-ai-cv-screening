-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 17, 2026 at 05:16 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `cv_screening`
--

-- --------------------------------------------------------

--
-- Table structure for table `applications`
--

CREATE TABLE `applications` (
  `id` char(36) NOT NULL,
  `job_id` char(36) NOT NULL,
  `candidate_id` char(36) NOT NULL,
  `cv_file_id` char(36) DEFAULT NULL,
  `status` enum('uploaded','processed','shortlisted','rejected') NOT NULL DEFAULT 'uploaded',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `applications`
--

INSERT INTO `applications` (`id`, `job_id`, `candidate_id`, `cv_file_id`, `status`, `created_at`, `updated_at`) VALUES
('7ca569e4-9df1-48a2-9317-1bd1d90dd484', '5464fb78-fe93-4f28-8dee-74b1c261d772', '95b9e599-f064-43df-98ec-d4b5cc5a6dd9', 'bc38a24b-9797-4db7-959a-e219172d80ce', 'processed', '2026-07-17 11:31:37', '2026-07-17 11:31:37'),
('d20fdce7-8ee3-4387-b3fe-d9795f4993a1', '5464fb78-fe93-4f28-8dee-74b1c261d772', '7d5f7789-7a48-4780-b024-1eef1accdd5f', '6a3252d5-7704-46a4-a718-c44682e1efb3', 'shortlisted', '2026-07-17 10:59:59', '2026-07-17 11:00:08');

-- --------------------------------------------------------

--
-- Table structure for table `candidates`
--

CREATE TABLE `candidates` (
  `id` char(36) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `address` varchar(500) DEFAULT NULL,
  `linkedin` varchar(500) DEFAULT NULL,
  `github` varchar(500) DEFAULT NULL,
  `portfolio` varchar(500) DEFAULT NULL,
  `years_of_experience` decimal(4,1) DEFAULT NULL,
  `communication_score` decimal(5,4) NOT NULL DEFAULT 0.5000,
  `education_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`education_json`)),
  `experience_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`experience_json`)),
  `projects_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`projects_json`)),
  `certifications_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`certifications_json`)),
  `languages_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`languages_json`)),
  `publications_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`publications_json`)),
  `awards_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`awards_json`)),
  `references_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`references_json`)),
  `soft_skills_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`soft_skills_json`)),
  `raw_text` mediumtext DEFAULT NULL,
  `extraction_meta` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`extraction_meta`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `candidates`
--

INSERT INTO `candidates` (`id`, `full_name`, `email`, `phone`, `address`, `linkedin`, `github`, `portfolio`, `years_of_experience`, `communication_score`, `education_json`, `experience_json`, `projects_json`, `certifications_json`, `languages_json`, `publications_json`, `awards_json`, `references_json`, `soft_skills_json`, `raw_text`, `extraction_meta`, `created_at`, `updated_at`) VALUES
('7d5f7789-7a48-4780-b024-1eef1accdd5f', 'Dilmi Rathnayake', 'dilmi.t.rathnayake@example.com', NULL, NULL, NULL, NULL, NULL, 5.0, 0.6930, '[{\"university\":\"University\",\"degree\":\"BSc Computer Science\",\"graduation_year\":\"2018\",\"field\":null}]', '[{\"company\":null,\"job_title\":\"Senior Developer at Acme Corp (2019-2024). Built recruitment analytics dashboards and ML pipelines.\",\"duration\":\"2019-2024\",\"description\":null}]', '[]', '[]', '[]', '[]', '[]', '[]', '[]', 'Dilmi Rathnayake\nEmail: alex.rivera@example.com | Phone: +1 555 0100\nSummary\nSoftware engineer with 5 years experience in Python, React, and MySQL.\nSkills\nPython, JavaScript, React, FastAPI, MySQL, Docker, NLP\nExperience\nSenior Developer at Acme Corp (2019-2024). Built recruitment analytics dashboards and ML pipelines.\nEducation\nBSc Computer Science, State University, 2018', '{\"source_method\":\"python-docx\",\"ner_loaded\":true,\"sections_found\":[\"summary\",\"skills\",\"experience\",\"education\"],\"communication_breakdown\":{\"readability\":0.2941,\"structure\":0.8,\"lexical_diversity\":1,\"spelling_proxy\":1},\"ner_entity_counts\":{\"SKILL\":3,\"DESIGNATION\":2}}', '2026-07-17 10:59:59', '2026-07-17 10:59:59'),
('95b9e599-f064-43df-98ec-d4b5cc5a6dd9', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0.6328, '[{\"university\":\"College 1994 Associate : Accounting City\",\"degree\":\"Bachelors degree.\",\"graduation_year\":\"1994\",\"field\":null}]', '[{\"company\":null,\"job_title\":\"Company Name July 2011 to November 2012 Accountant\",\"duration\":\"July 2011 to November 2012\",\"description\":null},{\"company\":null,\"job_title\":\"City , State\",\"duration\":null,\"description\":null},{\"company\":\"In this position as an Accountant assigned to the Defense Enterprise Accounting and Management System (DEAMS) ERO I was\",\"job_title\":\"Enterprise Resource Planning Office (ERO)\",\"duration\":null,\"description\":\"responsible for identifying and resolving issues affecting the DEAMS General Ledger. I worked with teammates from the Procure to Pay, Orders to Cash, and Budget to Report areas to resolve daily challenges encountered with the deployment of DEAMS to additional customers and when system change requests were promoted to production. I supported the testing of scripts, patches, and system change requests ensuring any anomalies were identified to the DEAMS Functional\"},{\"company\":null,\"job_title\":\"Company Name April 2010 to June 2011 Resource Advisor\",\"duration\":\"April 2010 to June 2011\",\"description\":null},{\"company\":\"In this position as Resource Advisor for the 1st Air Communications Operation Squadron (1ACOS) I was responsible for providing\",\"job_title\":\"City , State\",\"duration\":null,\"description\":\"financial advice and decision support to the Commander. I was responsible for coordinating a 4.6M budget between four funding sources. I coordinated with USAFE Directorate of Intelligence (USAFE/A2), USAFE Directorate of Air and Space Operations (USAFE/A3), USAFE Directorate of Communications (USAFE/A6) and the 435th Air Ground Operations Wing to ensure 1ACOS meets its mission\"},{\"company\":null,\"job_title\":\"Control Program, zero findings.\",\"duration\":null,\"description\":null},{\"company\":null,\"job_title\":\"During yearly audit by 700th CONS received zero findings.\",\"duration\":null,\"description\":null},{\"company\":null,\"job_title\":\"Company Name July 2008 to April 2010 Staff Accountant\",\"duration\":\"July 2008 to April 2010\",\"description\":null},{\"company\":\"In my position as the Staff Accountant for HQ USAFE I was responsible for providing accounting and financial oversight and advice to\",\"job_title\":\"City , State\",\"duration\":null,\"description\":\"customers throughout the Command in support of the USAFE Comptroller. I was responsible for performing ongoing analysis of financial programs to identify negative trends and weaknesses, ensured specific weaknesses were corrected, and determined whether systemic or repeat issues were identified and adequately addressed. I was required to apply a comprehensive knowledge of analysis/reporting requirements and data produced to resolve these issues.\"},{\"company\":\"This not only created rework, it delayed the payment of the invoices.\",\"job_title\":\"DFAS personnel.\",\"duration\":null,\"description\":\"I partnered with DFAS Denver, corrected the records in the Access On-Line accounts eliminating the error condition. I identified a method to deliver one-on-one training in support of the USAFE deployment of the Open Document Analysis (ODA) tool in\"},{\"company\":\"By utilizing Defense Connect Online I provided training remotely, virtually eliminating the need to expend funds on Temporary Duty (TDY)\",\"job_title\":\"FMSuite.\",\"duration\":\"January 2007 to July 2009\",\"description\":\"travel. The results of this training produced results that went well above expectations and were noted by the ODA Program Management Office. Company Name January 2007 to July 2009 Chief, Reports Branch. Accounts Maintenance and Control\"},{\"company\":\"In my position as Chief of the Reports Branch in Accounts Maintenance Control (AM C) I was responsible for ensuring the\",\"job_title\":\"City , State\",\"duration\":null,\"description\":\"development and standardization of various managerial and system reports. I was responsible for the completeness and accuracy of weekly, monthly, quarterly, semi-annual, and annual reports. My branch monitored errors in the General Accounting and Finance System (GAFS/BQ) and ensured corrective actions were accomplished.\"}]', '[]', '[\"Certified Defense Financial Manager\",\"CDFM\",\"May 2005\",\"Interests\",\"American Society Of Military Comptrollers\",\"Additional Information\"]', '[]', '[]', '[]', '[]', '[]', 'ACCOUNTANT\nSummary\nFinancial Accountant specializing in financial planning, reporting and analysis within the Department of Defense.\nHighlights\nAccount reconciliations\nResults-oriented\nFinancial reporting\nCritical thinking\nAccounting operations professional\nAnalysis of financial systems\nERP (Enterprise Resource Planning) software.\nExcellent facilitator\nAccomplishments\nServed on a tiger team which identified and resolved General Ledger postings in DEAMS totaling 360B in accounting adjustments. This allowed\nfor the first successful fiscal year-end close for 2012.\nIn collaboration with DFAS Europe, developed an automated tool that identified duplicate obligations. This tool allowed HQ USAFE to\ndeobligate over 5M in duplicate obligations.\nExperience\nCompany Name July 2011 to November 2012 Accountant\nCity , State\nEnterprise Resource Planning Office (ERO)\nIn this position as an Accountant assigned to the Defense Enterprise Accounting and Management System (DEAMS) ERO I was\nresponsible for identifying and resolving issues affecting the DEAMS General Ledger.\nI worked with teammates from the Procure to Pay, Orders to Cash, and Budget to Report areas to resolve daily challenges encountered\nwith the deployment of DEAMS to additional customers and when system change requests were promoted to production.\nI supported the testing of scripts, patches, and system change requests ensuring any anomalies were identified to the DEAMS Functional\nManagement Office for action by the DEAMS Program Management Office and/or the System Integrator.\nIn addition, I served on a tiger team designed to identify and resolve General Ledger posting differences and supported the development of\n360B in accounting adjustments allowing for the first successful fiscal year-end close in 2012.\nThese actions also allowed for the reconciliation and closure of fiscal year 2010 and 2011 accounting adjustments ensuring that all DEAMS\nfiscal year-end requirements were completed.\nThese actions were recognized as critical to the successful review report issued by the Air Force Operational Test and Evaluation Center\n(AFOTEC) resulting in the Air Force receiving the authority to continue with the deployment of DEAMS.\nCompany Name April 2010 to June 2011 Resource Advisor\nCity , State\nIn this position as Resource Advisor for the 1st Air Communications Operation Squadron (1ACOS) I was responsible for providing\nfinancial advice and decision support to the Commander.\nI was responsible for coordinating a 4.6M budget between four funding sources.\nI coordinated with USAFE Directorate of Intelligence (USAFE/A2), USAFE Directorate of Air and Space Operations (USAFE/A3),\nUSAFE Directorate of Communications (USAFE/A6) and the 435th Air Ground Operations Wing to ensure 1ACOS meets its mission\nrequirements.\nI consistently managed three separate timelines for providing budget/unfunded requirements, providing documentation and various reports in\nthe required format for each organization.\nI discussed the outcome of the Group and Directorate budget meetings providing feedback the same day to the Flight Chiefs and CC any\nissue which affects 1ACOS directly.\nI monitored the Defense Travel System (DTS) daily and identify orders and authorizations needing approval and provided notification to the\nappropriate Reviewing Officials and Approvers.\nUtilizing DTS and the General Accounting and Finance System I reviewed status reports to identify anomalies in obligations and have\nidentified those orders which require correction prior to payment.\nI provided Government Purchase Card (GPC) status reports the same day they are requested and in addition, communicated with the\nappropriate cardholders when changes were required to support their program.\nI identified cardholder training requirements and monitored these requirements to ensure all required training was completed in support of\nthis mission critical program.\nI developed guidance for the GPC cardholders on procedures for requesting training for the squadron and in addition I provided answers to\ncardholder questions on unique or non-standard issues/concerns.\n\n Assumed the role of the Billing Official during my final rating period and completed a self inspection of the program for the Management\nControl Program, zero findings.\nDuring yearly audit by 700th CONS received zero findings.\nCompany Name July 2008 to April 2010 Staff Accountant\nCity , State\nIn my position as the Staff Accountant for HQ USAFE I was responsible for providing accounting and financial oversight and advice to\ncustomers throughout the Command in support of the USAFE Comptroller.\nI was responsible for performing ongoing analysis of financial programs to identify negative trends and weaknesses, ensured specific\nweaknesses were corrected, and determined whether systemic or repeat issues were identified and adequately addressed.\nI was required to apply a comprehensive knowledge of analysis/reporting requirements and data produced to resolve these issues.\nIn collaboration with DFAS Europe, developed an automated tool that identifies duplicate obligations by comparing records in the\naccounting system to the contracting system and provided notification to the funds manager for review and resolution.\nThis tool eliminated hours of manual research and results allowed HQ USAFE to deobligate over 5M in duplicate obligations.\nI was responsible for establishing various performance metrics which ensured effective and efficient use of USAFE financial resources.\nI supported the USAFE/FMA Financial metrics program by collaborating with DFAS Limestone in the development of an automated tool\nthat provided senior leaders with visibility to any USAFE unit that is not in compliance with the established rules and regulations related to\nthe GPC.\nThis tool provides management reports that are used to populate the monthly metric charts which are briefed by the USAFE/FMA.\nThis tool provided the capability for USAFE/FMA to collaborate with USAFE Contracting and develop/deploy joint guidance that supports\nthe established Air Force Instruction mandating card suspension for card holders who are not in compliance with required reservation of\nfunds in the entitlement system in support of the GPC.\nI identified and resolved a problem with five GPC accounts that had been rejecting during the automated interface process each month.\nMy research revealed that these accounts were rejecting for invalid paying station and required manual intervention by both Wing and\nDFAS personnel.\nThis not only created rework, it delayed the payment of the invoices.\nI partnered with DFAS Denver, corrected the records in the Access On-Line accounts eliminating the error condition.\nI identified a method to deliver one-on-one training in support of the USAFE deployment of the Open Document Analysis (ODA) tool in\nFMSuite.\nBy utilizing Defense Connect Online I provided training remotely, virtually eliminating the need to expend funds on Temporary Duty (TDY)\ntravel.\nThe results of this training produced results that went well above expectations and were noted by the ODA Program Management Office.\nCompany Name January 2007 to July 2009 Chief, Reports Branch. Accounts Maintenance and Control\nCity , State\nIn my position as Chief of the Reports Branch in Accounts Maintenance Control (AM C) I was responsible for ensuring the\ndevelopment and standardization of various managerial and system reports.\nI was responsible for the completeness and accuracy of weekly, monthly, quarterly, semi-annual, and annual reports.\nMy branch monitored errors in the General Accounting and Finance System (GAFS/BQ) and ensured corrective actions were\naccomplished.\nI also ensured fund balances were reconciled and reports were verified prior to release to base activities and higher headquarters.\nLimestone reorganized under the High Performing Organization (HPO) in January 2007 and at that time I was reassigned to AM C, a\nDirectorate which previously did not exist.\nMy challenge during that time was to staff my branch, implement an aggressive training schedule, and ensure the continuity of financial\nreporting was maintained.\nAs we transitioned into the HPO we continued defining the missions and functions for AM C for the entire network.\nI participated in biweekly conference calls with Standards and Compliance in an effort to define missions and functions for AM C.\nWorked with management in determining FTEs needed for the branch.\nI was responsible for developing meaningful performance standards for my employees since this branch and its functions did not previously\nexist.\nLimestone POC for an initiative to eliminate suspense accounts throughout the agency.\nIdentified suspense accounts not initially targeted, formulated strategies to eliminate accounts or requested waivers, and participated in plans\nto modify processes using suspense accounts, such as the interfund suspense account.\nThese actions provided initial progress towards meeting the Department of Treasury s mandate to discontinue suspense accounts by\nFebruary 2009.\nWorked with staff to reduce reconciliations from 6.9 million in February 2007 to 1.1 million in August, accomplished this despite loss in\nexperienced personnel and realigning resources to support critical initiatives in Accounts Payable.\nI orchestrated the transition of reporting requirements for the Transportation Financial Management System (TFMS) workload from DFAS\nOmaha to Limestone.\nAfter transition to Limestone encouraged staff responsible for these reports to streamline the processes.\nStaff automated a completely manual, time consuming process, thus eliminating potential key stroke errors and manually validating numerous\nspreadsheets and listings.\nContributor to Federal Managers Financial Integrity Act (FMFIA) Compliance Review and establishment of assessable units.\n\n Identified inconsistencies in information provided by staff on foreign currency fluctuation adjustments.\nPersisted in getting higher level review of regulatory and policy guidance.\nReport of foreign currency fluctuation is now consistently accurate.\nCompany Name February 2000 to January 2007 Chief, Accounts Payable Branch\nCity , State\nAs Chief Of Accounts Payable I was responsible for the overall management of a branch consisting of over 120 employees.\nMy four first line supervisors were responsible for establishing priorities, schedules, and work assignments ensuring changes in workload are\naccounted for to minimize the impact on normal office operations.\nWe consistently reviewed these areas and made necessary personnel moves based on shifting priorities.\nThis was extremely important during the DFAS Denver directed database consolidations and with the assumption of the Air National Guard\nworkload.\nWorkload increased rapidly while staffing increased gradually, which dictated frequent priority changes and personnel moves.\nI also worked closely with the Major Commands supported by DFAS Limestone strengthening our partnership when workload spikes\nnegatively impacted our customers.\nIn December 2004, our overaged invoice percentage was nearing 25 and we had a backlog of vendor pay documents exceeding 30,000.\nBy working with the DFAS Command Client Executives and the Major Command Comptrollers, I was instrumental in forming a strategy\nthat included soliciting Air Force personnel assistance in document processing, identification of must pay now bills, and the formation of\nspecial action response teams dedicated to responding to our customer s most urgent requirements.\nAs a result of these efforts, in a three month period, we were able to reduce our overaged invoice percentage by 19 and our backlog of\ndocuments to no documents over 20 days old thereby minimizing the adverse impact on customer funds.\nI was responsible for providing personnel feedback sessions quarterly and prepared supervisory appraisals of employees performance and\npotential for advancement.\nPartnering with the management staff and employees, I was instrumental in establishing Employee Performance Plans that linked employee\nperformance to established DFAS Strategies and Balance Scorecard goals.\nIn this position as a supervisory accountant I was responsible for performing ongoing analysis of the Vendor Pay workflow and production\nto identify negative trends and weaknesses, ensure specific weaknesses have been corrected, and determine whether systemic or repeat\nissues have been identified and adequately addressed.\nI was required to apply a comprehensive knowledge of analysis/reporting requirements, work processes, vendor pay system structures, and\ndata produced to resolve these issues.\nUtilizing my expertise with Louis II data retrieval software, I produced ad-hoc data queries for in-house and external use by our customers.\nThese retrievals were designed to reduce the man- hours necessary to perform complex finance and accounting functions by DFAS and Air\nForce personnel.\nI was responsible for the budget resources necessary to operate the branch.\nIn this capacity, I prepared budget over execution justifications, plan and monitor overtime costs, and control supply purchases to ensure the\nmost cost efficient operation possible.\nI was required to respond to inquiries from various sources, which include, but are not limited to, vendors, DFAS management, accounting\nliaison offices, resource advisors, and other DFAS field sites.\nThese inquiries required my ability to relay technical aspects of systems deficiencies to customers who are not familiar with our operation.\nI participated in video teleconferences, conference calls, and briefings designed to address customer and DFAS management requirements.\nI was called upon to explain, in laymen s terms, DFAS policy and procedures with regards to delays in payment due to various reasons.\nI responded to various audit reports and studies ensuring senior management and audit personnel, understand particular situations within the\nVendor Pay business process that result in these findings.\nCompany Name February 1999 to February 2000 Chief, Recon and Reports Branch\nCity , State\nIn my position as Chief, Vendor Pay Reports and Recon Branch, I exercised supervision (either directly or indirectly) over 22 employees\nprimarily in the 525 series in grades ranging from GS-5 through GS-8.\nThis responsibility also included supervision of the German local national workers assigned to my duty section.\nI was responsible for planning, directing, and supervising the activities of the work force in the review, interpretation, processing, and\nreconciliation of vendor pay and accounting data and the production of timely and accurate financial statement report requirements.\nI participated in the development of branch policies continually reviewing and evaluating the organizational operations, work distribution, and\nprocedures.\nI coordinated the activities of the assigned functions with those of other organizations to obtain the most effective correlation of financial\ndata.\nDirected and provided technical guidance to subordinates in the assigned area.\nAssured the timeliness and accuracy of assigned workload.\nPlanned, organized, directed, coordinated, and reviewed the work of subordinate s sections ensuring the mission and functions of the\ndivision were carried out.\nI managed and realigned resources, conducted program analyses, and made decisions in accordance with unit cost principles, outputs,\ntargets, and changing budgetary constraints.\nI participated in long range planning, goal setting, and evaluating the subordinate staff.\nInterpreted and clarified branch policies and resolved operational problems.\nEnsured efficient utilization and professional development of my staff.\n\n I was expected to provide reasonable assurance that operations were conducted in compliance with applicable laws and that funds,\nproperty, and other assets were safeguarded against waste, loss, unauthorized use, or misappropriation.\nI ensured continuing and affirmative application and support of DoD and DFAS policy concerning the equal opportunity and affirmative\naction programs.\nEnsured personnel management within organizational entity under my supervision was accomplished without regard to race, color, religion,\nsex, age, national origin, or handicap.\nI kept abreast of developments, policy issuance, and other similar material in the equal opportunity field and fully supported the DoD and\nDFAS Equal Opportunity Program.\nI was responsible and accountable for the safety and health of my subordinates.\nI ensured personnel were trained to work safely.\nI enforced safety and health rules, corrected unsafe or unhealthy acts and unsafe or unhealthy mechanical or physical conditions, investigated\nmishaps and tool other actions necessary to ensure the safety and health of my employees.\nCompany Name June 1995 to February 1999 Chief, Accounts Payable Branch\nCity , State\nI was responsible for establishing priorities, schedules, and work assignments ensuring changes in workload are accounted for to minimize\nthe impact on normal office operations.\nThis was important during the DFAS Denver directed workload realighment to the Field Sites servicing our customers by Major Command.\nWorkload increased which dictated frequent priority changes and personnel moves.\nI also worked closely with the Major Commands supported by DFAS Limestone strengthening our partnership when workload spikes\nnegatively impacted our customers.\nI was responsible for providing personnel feedback sessions quarterly and preparedsupervisory appraisals of employees performance and\npotential for advancement.\nAs a supervisory accountant I was responsible for performing ongoing analysis of the Vendor Pay workflow and production.\nI identified negative trends and weaknesses, ensured specific weaknesses were corrected, and determine whether systemic or repeat issues\nwere identified and adequately addressed.\nI was required to apply a comprehensive knowledge of analysis/reporting requirements, work processes, vendor pay system structures, and\ndata produced to resolve these issues.\nUtilizing my knowledge with Louis II data retrieval software, I produced ad-hoc data queries for in-house and external use by our\ncustomers.\nThese retrievals are all designed to reduce the man- hours necessary to perform complex finance and accounting functions by DFAS and\nAir Force personnel.\nI was responsible for the budget resources necessary to operate the branch.\nIn this capacity, I prepared budget over execution justifications, plan and monitor overtime costs, and control supply purchases to ensure the\nmost cost efficient operation possible.\nI was required to respond to inquiries from various sources, which include, but are not limited to, vendors, DFAS management, accounting\nliaison offices, resource advisors, and other DFAS field sites.\nThese inquiries require my ability to relay technical aspects of systems deficiencies to customers who are not familiar with our operation.\nI participated in video teleconferences, conference calls, and briefings designed to address customer and DFAS management requirements.\nI was often called upon to explain, in laymen s terms, DFAS policy and procedures with regards to delays in payment due to various\nreasons.\nI was required to respond to various audit reports and studies ensuring senior management and audit personnel, understand particular\nsituations within the Vendor Pay business process that result in these findings.\nI was hand selected by the Field Site Director and Vendor Pay Site Manager to represent DFAS Limestone on a team comprised of\nrepresentatives from all DFAS Denver field sites to provide training to our Air Force base level Resource Advisors.\nDuring a five week period, I provided Boot Camp training to over 400 base level personnel ensuring resource advisors were familiar with\nthe DFAS structure and mission requirements related to funds management.\nCompany Name June 1994 to June 1995 Accountant, Network Assistant Team\nCity , State\nAs a member of the Network Assistance Team, I was required to have an extensive working knowledge of DoD accounting systems,\ntheory, policy, and procedures.\nI was consistently called upon to develop and implement procedures consistent with DoD regulations.\nCoordinated with DFAS Denver and the Omaha Field Site on the consolidation of the first geographically separated Defense Accounting\nOffice into DFAS.\nIn my position as a member of the Network Assistance Team I was required, upon arrival at each base level Defense Accounting Office\n(DAO) to provide an in-brief.\nThis briefing identified team members, the purpose of the visit, goals, and responsibilities.\nUpon completion of the assignment, provided a written and oral out-brief outlining the team accomplishments during the visit.\nI provided recommendations to preclude recurring problems and to prepare the organization for consolidation.\nCompany Name June 1993 to June 1994 Supervisor, Accounts Control Branch\nCity , State\nI directed/supervised the accomplishment ofallfinancialreports and statements\n\n I directed/supervised the accomplishment of all financial reports and statements.\nI was responsible for the completeness and accuracy of weekly, monthly, quarterly, semi-annual, and annual reports.\nMonitored errors in the General Accounting and Finance System (GAFS/BQ) and ensured corrective actions were accomplished.\nI also ensured fund balances were reconciled to the appropriate audit listings and verified reports prior to release to base activities and\nhigher headquarters.\nI furnished accounting data to base organizations often interpreting and analyzing the data to help funds managers resolve problems and\nmanage their programs more effectively.\nI attended Major Command (MAJCOM) and Headquarters level workshops to participate and contribute to accounting policy and system\nchanges.\nI provided professional assistance to Data Automation relevant to processing of accounting and finance data, interpreting deficiencies in\nsoftware based on output products and system related problems.\nI utilized my working knowledge of commercial and government accounting system principles and knowledge of Processing Centers (PCs)\nto review, verify, analyze, and evaluate accounting and finance operations.\nWhile serving as Chief, Account Control I ensured areas of concern were addressed, concentrating on problem areas related to the\ndatabase.\nI analyzed computer output products to determine processing deficiencies.\nThey included, but were not limited to, the Open Document Listing (ODL), Operating Budget Ledger (OBL), Allotment Ledger (AL), and\nthe Accounting and Finance Workload Information Management System (A F WIMS) Extract list.\nI provided technical assistance related to policy and procedural.\nchanges required as a result of the impending base closure.\nAnalyzed/developed and recommended improved training procedures enabling better use of system procedures ensuring governing\ndirectives were followed.\nI evaluated accuracy of accounting records prior to fiscal year closeout ensuring the Accounting and Finance Officer could certify their\naccuracy as required by regulation.\nExamined accounting transactions and documents to ensure they conformed to established accounting policy and principles.\nCoordinated and directed fiscal year end conversion for the GAFS and Integrated Accounts Payable System (IAPS).\nEducation\nNorthern Maine Community College 1994 Associate : Accounting City , State , USA\nEmphasis in Business\n1994 Associates : Accounting City , State , USA GPA: GPA: 3.41\nAccounting GPA: 3.41 174 Hours, Quarter\nAttended Husson College, major Accounting 78 semester hours toward Bachelors degree.\nProfessional Military Comptroller School, 6wk, 4-98 Managerial Accounting I, 09-98 Interested-Based Bargaining Training for Management,\n24hrs, 09-01 Auditing Methods and Concepts 09-98 Organizational Leadership, 32hrs, 07-03 Management Development II, 32hrs, 07-03.\nCertifications\nCertified Defense Financial Manager, CDFM, May 2005\nInterests\nAmerican Society Of Military Comptrollers\nAdditional Information\nSkills\nAccounting General Accounting Accounts Payable Program Management.', '{\"source_method\":\"pymupdf\",\"ner_loaded\":true,\"sections_found\":[\"summary\",\"experience\",\"education\",\"certifications\",\"skills\"],\"communication_breakdown\":{\"readability\":0.172,\"structure\":0.95,\"lexical_diversity\":0.6899,\"spelling_proxy\":0.9971},\"ner_entity_counts\":{\"SKILL\":5}}', '2026-07-17 11:31:37', '2026-07-17 11:31:37');

-- --------------------------------------------------------

--
-- Table structure for table `candidate_skills`
--

CREATE TABLE `candidate_skills` (
  `candidate_id` char(36) NOT NULL,
  `skill_id` int(10) UNSIGNED NOT NULL,
  `skill_type` enum('technical','soft') NOT NULL DEFAULT 'technical'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `candidate_skills`
--

INSERT INTO `candidate_skills` (`candidate_id`, `skill_id`, `skill_type`) VALUES
('7d5f7789-7a48-4780-b024-1eef1accdd5f', 1, 'technical'),
('7d5f7789-7a48-4780-b024-1eef1accdd5f', 2, 'technical'),
('7d5f7789-7a48-4780-b024-1eef1accdd5f', 3, 'technical'),
('7d5f7789-7a48-4780-b024-1eef1accdd5f', 4, 'technical'),
('7d5f7789-7a48-4780-b024-1eef1accdd5f', 5, 'technical'),
('7d5f7789-7a48-4780-b024-1eef1accdd5f', 6, 'technical'),
('7d5f7789-7a48-4780-b024-1eef1accdd5f', 7, 'technical'),
('95b9e599-f064-43df-98ec-d4b5cc5a6dd9', 8, 'technical'),
('95b9e599-f064-43df-98ec-d4b5cc5a6dd9', 9, 'technical'),
('95b9e599-f064-43df-98ec-d4b5cc5a6dd9', 10, 'technical'),
('95b9e599-f064-43df-98ec-d4b5cc5a6dd9', 11, 'technical'),
('95b9e599-f064-43df-98ec-d4b5cc5a6dd9', 12, 'technical');

-- --------------------------------------------------------

--
-- Table structure for table `cv_files`
--

CREATE TABLE `cv_files` (
  `id` char(36) NOT NULL,
  `candidate_id` char(36) DEFAULT NULL,
  `original_filename` varchar(255) NOT NULL,
  `stored_filename` varchar(255) NOT NULL,
  `mime_type` varchar(120) DEFAULT NULL,
  `file_path` varchar(500) NOT NULL,
  `file_size_bytes` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `extraction_status` enum('pending','success','failed') NOT NULL DEFAULT 'pending',
  `extraction_error` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `cv_files`
--

INSERT INTO `cv_files` (`id`, `candidate_id`, `original_filename`, `stored_filename`, `mime_type`, `file_path`, `file_size_bytes`, `extraction_status`, `extraction_error`, `created_at`) VALUES
('6a3252d5-7704-46a4-a718-c44682e1efb3', '7d5f7789-7a48-4780-b024-1eef1accdd5f', '_smoke_cv.docx', '1784285998652-704aa8ee-c162-47a7-9381-cf9cef315c29.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'd:\\client_projects\\cv_screening\\backend\\uploads\\cvs\\1784285998652-704aa8ee-c162-47a7-9381-cf9cef315c29.docx', 35569, 'success', NULL, '2026-07-17 10:59:59'),
('bc38a24b-9797-4db7-959a-e219172d80ce', '95b9e599-f064-43df-98ec-d4b5cc5a6dd9', '10554236.pdf', '1784287897617-6f4917f5-2460-4b0f-8d0d-1d8196222060.pdf', 'application/pdf', 'd:\\client_projects\\cv_screening\\backend\\uploads\\cvs\\1784287897617-6f4917f5-2460-4b0f-8d0d-1d8196222060.pdf', 48278, 'success', NULL, '2026-07-17 11:31:37');

-- --------------------------------------------------------

--
-- Table structure for table `hr_managers`
--

CREATE TABLE `hr_managers` (
  `id` char(36) NOT NULL,
  `user_id` char(36) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `company` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `hr_managers`
--

INSERT INTO `hr_managers` (`id`, `user_id`, `full_name`, `company`, `phone`, `created_at`, `updated_at`) VALUES
('33333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222222', 'Sample HR Manager', 'Demo Recruitment Ltd', '+94 77 000 0000', '2026-07-17 10:49:00', '2026-07-17 10:49:00');

-- --------------------------------------------------------

--
-- Table structure for table `interviews`
--

CREATE TABLE `interviews` (
  `id` char(36) NOT NULL,
  `application_id` char(36) NOT NULL,
  `job_id` char(36) NOT NULL,
  `candidate_id` char(36) NOT NULL,
  `scheduled_at` datetime NOT NULL,
  `duration_minutes` int(10) UNSIGNED NOT NULL DEFAULT 45,
  `mode` enum('online','onsite','phone') NOT NULL DEFAULT 'online',
  `meeting_link` varchar(500) DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `status` enum('scheduled','rescheduled','completed','cancelled','no_show') NOT NULL DEFAULT 'scheduled',
  `notes` text DEFAULT NULL,
  `calendar_event_id` varchar(255) DEFAULT NULL,
  `n8n_workflow_ref` varchar(255) DEFAULT NULL,
  `created_by` char(36) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `interviews`
--

INSERT INTO `interviews` (`id`, `application_id`, `job_id`, `candidate_id`, `scheduled_at`, `duration_minutes`, `mode`, `meeting_link`, `location`, `status`, `notes`, `calendar_event_id`, `n8n_workflow_ref`, `created_by`, `created_at`, `updated_at`) VALUES
('f38e6307-aae2-450f-ae78-415a88cb5240', 'd20fdce7-8ee3-4387-b3fe-d9795f4993a1', '5464fb78-fe93-4f28-8dee-74b1c261d772', '7d5f7789-7a48-4780-b024-1eef1accdd5f', '2026-07-24 11:00:08', 45, 'online', 'https://meet.example.com/smoke', NULL, 'scheduled', 'Phase 6 smoke test', NULL, NULL, '22222222-2222-2222-2222-222222222222', '2026-07-17 11:00:08', '2026-07-17 11:00:08');

-- --------------------------------------------------------

--
-- Table structure for table `jobs`
--

CREATE TABLE `jobs` (
  `id` char(36) NOT NULL,
  `hr_manager_id` char(36) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `minimum_experience` decimal(4,1) NOT NULL DEFAULT 0.0,
  `education_level` varchar(100) DEFAULT NULL,
  `industry` varchar(50) NOT NULL DEFAULT 'default',
  `required_certifications` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`required_certifications`)),
  `ranking_weights` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`ranking_weights`)),
  `communication_importance` decimal(3,2) DEFAULT NULL,
  `status` enum('draft','active','closed') NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `jobs`
--

INSERT INTO `jobs` (`id`, `hr_manager_id`, `title`, `description`, `minimum_experience`, `education_level`, `industry`, `required_certifications`, `ranking_weights`, `communication_importance`, `status`, `created_at`, `updated_at`) VALUES
('5464fb78-fe93-4f28-8dee-74b1c261d772', '33333333-3333-3333-3333-333333333333', 'Phase6 Smoke Software Engineer', 'Need Python React MySQL engineer for CV screening platform.', 0.0, 'bachelor', 'technology', '[]', '{\"technical_skills\":0.25,\"experience\":0.25,\"projects\":0.1,\"education\":0.15,\"communication\":0.15,\"certifications\":0.1}', NULL, 'active', '2026-07-17 10:59:58', '2026-07-17 10:59:58');

-- --------------------------------------------------------

--
-- Table structure for table `job_skills`
--

CREATE TABLE `job_skills` (
  `job_id` char(36) NOT NULL,
  `skill_id` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `job_skills`
--

INSERT INTO `job_skills` (`job_id`, `skill_id`) VALUES
('5464fb78-fe93-4f28-8dee-74b1c261d772', 1),
('5464fb78-fe93-4f28-8dee-74b1c261d772', 2),
('5464fb78-fe93-4f28-8dee-74b1c261d772', 3);

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` char(36) NOT NULL,
  `user_id` char(36) DEFAULT NULL,
  `candidate_id` char(36) DEFAULT NULL,
  `type` varchar(50) NOT NULL,
  `title` varchar(255) NOT NULL,
  `body` text DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`id`, `user_id`, `candidate_id`, `type`, `title`, `body`, `is_read`, `created_at`) VALUES
('f790cea8-3773-47b2-88f9-547e96da811f', '22222222-2222-2222-2222-222222222222', '7d5f7789-7a48-4780-b024-1eef1accdd5f', 'interview_scheduled', 'Interview scheduled: Dilmi Rathnayake', 'Phase6 Smoke Software Engineer at 2026-07-24T11:00:08.733Z', 0, '2026-07-17 11:00:08');

-- --------------------------------------------------------

--
-- Table structure for table `ranking_results`
--

CREATE TABLE `ranking_results` (
  `id` char(36) NOT NULL,
  `application_id` char(36) NOT NULL,
  `job_id` char(36) NOT NULL,
  `candidate_score` decimal(8,4) NOT NULL,
  `matching_percentage` decimal(6,2) NOT NULL,
  `ranking_position` int(10) UNSIGNED NOT NULL,
  `semantic_similarity` decimal(8,4) DEFAULT NULL,
  `ranking_explanation` text DEFAULT NULL,
  `criterion_scores` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`criterion_scores`)),
  `weights_used` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`weights_used`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `ranking_results`
--

INSERT INTO `ranking_results` (`id`, `application_id`, `job_id`, `candidate_score`, `matching_percentage`, `ranking_position`, `semantic_similarity`, `ranking_explanation`, `criterion_scores`, `weights_used`, `created_at`) VALUES
('c9b529db-ebf6-4ed2-b2c7-e1dfbcdc6f55', '7ca569e4-9df1-48a2-9317-1bd1d90dd484', '5464fb78-fe93-4f28-8dee-74b1c261d772', 0.3285, 32.85, 2, 0.0879, 'Overall match 32.85% for \'Phase6 Smoke Software Engineer\' (technology). Top drivers: education=0.79×0.15, communication=0.63×0.15, experience=0.29×0.25. Semantic similarity=0.09.', '[{\"criterion\":\"technical_skills\",\"score\":0.0611,\"weight\":0.25,\"weighted_score\":0.0153,\"explanation\":\"Skills score 0.06. Matched: [\'none\']. Missing: [\'MySQL\', \'Python\', \'React\'].\"},{\"criterion\":\"experience\",\"score\":0.2923,\"weight\":0.25,\"weighted_score\":0.0731,\"explanation\":\"Candidate experience 0y vs required 0.0y (score=0.29).\"},{\"criterion\":\"projects\",\"score\":0.1882,\"weight\":0.1,\"weighted_score\":0.0188,\"explanation\":\"0 projects with tech overlap score 0.19.\"},{\"criterion\":\"education\",\"score\":0.7921,\"weight\":0.15,\"weighted_score\":0.1188,\"explanation\":\"Education match score 0.79 against \'bachelor\'.\"},{\"criterion\":\"communication\",\"score\":0.6328,\"weight\":0.15,\"weighted_score\":0.0949,\"explanation\":\"CV communication quality proxy score 0.63.\"},{\"criterion\":\"certifications\",\"score\":0.5,\"weight\":0.1,\"weighted_score\":0.05,\"explanation\":\"Certification match score 0.50 (6 listed).\"}]', '{\"technical_skills\":0.25,\"experience\":0.25,\"projects\":0.1,\"education\":0.15,\"communication\":0.15,\"certifications\":0.1}', '2026-07-17 11:31:47'),
('ebcfb6f1-aaed-4b95-80cc-f951139e2f16', 'd20fdce7-8ee3-4387-b3fe-d9795f4993a1', '5464fb78-fe93-4f28-8dee-74b1c261d772', 0.5877, 58.77, 1, 0.6074, 'Overall match 58.77% for \'Phase6 Smoke Software Engineer\' (technology). Top drivers: technical_skills=0.79×0.25, education=0.78×0.15, experience=0.46×0.25. Semantic similarity=0.61.', '[{\"criterion\":\"technical_skills\",\"score\":0.794,\"weight\":0.25,\"weighted_score\":0.1985,\"explanation\":\"Skills score 0.79. Matched: [\'MySQL\', \'Python\', \'React\']. Missing: [\'none\'].\"},{\"criterion\":\"experience\",\"score\":0.4639,\"weight\":0.25,\"weighted_score\":0.116,\"explanation\":\"Candidate experience 5.0y vs required 0.0y (score=0.46).\"},{\"criterion\":\"projects\",\"score\":0.1882,\"weight\":0.1,\"weighted_score\":0.0188,\"explanation\":\"0 projects with tech overlap score 0.19.\"},{\"criterion\":\"education\",\"score\":0.7798,\"weight\":0.15,\"weighted_score\":0.117,\"explanation\":\"Education match score 0.78 against \'bachelor\'.\"},{\"criterion\":\"communication\",\"score\":0.693,\"weight\":0.15,\"weighted_score\":0.1039,\"explanation\":\"CV communication quality proxy score 0.69.\"},{\"criterion\":\"certifications\",\"score\":0.3,\"weight\":0.1,\"weighted_score\":0.03,\"explanation\":\"Certification match score 0.30 (0 listed).\"}]', '{\"technical_skills\":0.25,\"experience\":0.25,\"projects\":0.1,\"education\":0.15,\"communication\":0.15,\"certifications\":0.1}', '2026-07-17 11:00:08');

-- --------------------------------------------------------

--
-- Table structure for table `skills`
--

CREATE TABLE `skills` (
  `id` int(10) UNSIGNED NOT NULL,
  `name` varchar(120) NOT NULL,
  `normalized` varchar(120) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `skills`
--

INSERT INTO `skills` (`id`, `name`, `normalized`, `created_at`) VALUES
(1, 'Python', 'python', '2026-07-17 10:59:58'),
(2, 'React', 'react', '2026-07-17 10:59:58'),
(3, 'MySQL', 'mysql', '2026-07-17 10:59:58'),
(4, 'JavaScript', 'javascript', '2026-07-17 10:59:59'),
(5, 'FastAPI', 'fastapi', '2026-07-17 10:59:59'),
(6, 'Docker', 'docker', '2026-07-17 10:59:59'),
(7, 'NLP', 'nlp', '2026-07-17 10:59:59'),
(8, 'Critical thinking', 'critical thinking', '2026-07-17 11:31:37'),
(9, 'ERP (Enterprise Resource Planning) software.', 'erp (enterprise resource planning) software.', '2026-07-17 11:31:37'),
(10, 'Accounts Control Branch', 'accounts control branch', '2026-07-17 11:31:37'),
(11, 'Allotment Ledger (AL)', 'allotment ledger (al)', '2026-07-17 11:31:37'),
(12, 'American Society Of Military Comptrollers', 'american society of military comptrollers', '2026-07-17 11:31:37');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` char(36) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','hr') NOT NULL DEFAULT 'hr',
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `email`, `password_hash`, `role`, `is_active`, `created_at`, `updated_at`) VALUES
('11111111-1111-1111-1111-111111111111', 'admin@cvscreening.local', '$2a$10$UfC2mh3z.Dkgi4fMxI2cEe.snKCkLqXx0I0Lecq9llbvP34.d4Ope', 'admin', 1, '2026-07-17 10:49:00', '2026-07-17 10:49:00'),
('22222222-2222-2222-2222-222222222222', 'hr@cvscreening.local', '$2a$10$UfC2mh3z.Dkgi4fMxI2cEe.snKCkLqXx0I0Lecq9llbvP34.d4Ope', 'hr', 1, '2026-07-17 10:49:00', '2026-07-17 10:49:00');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `applications`
--
ALTER TABLE `applications`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_application_job_candidate` (`job_id`,`candidate_id`),
  ADD KEY `idx_app_job` (`job_id`),
  ADD KEY `idx_app_status` (`status`),
  ADD KEY `fk_app_candidate` (`candidate_id`),
  ADD KEY `fk_app_cv` (`cv_file_id`);

--
-- Indexes for table `candidates`
--
ALTER TABLE `candidates`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_candidates_email` (`email`);

--
-- Indexes for table `candidate_skills`
--
ALTER TABLE `candidate_skills`
  ADD PRIMARY KEY (`candidate_id`,`skill_id`,`skill_type`),
  ADD KEY `fk_cs_skill` (`skill_id`);

--
-- Indexes for table `cv_files`
--
ALTER TABLE `cv_files`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_cv_candidate` (`candidate_id`);

--
-- Indexes for table `hr_managers`
--
ALTER TABLE `hr_managers`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_hr_user` (`user_id`);

--
-- Indexes for table `interviews`
--
ALTER TABLE `interviews`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_interview_job` (`job_id`),
  ADD KEY `idx_interview_candidate` (`candidate_id`),
  ADD KEY `idx_interview_scheduled` (`scheduled_at`),
  ADD KEY `fk_interview_app` (`application_id`);

--
-- Indexes for table `jobs`
--
ALTER TABLE `jobs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_jobs_hr` (`hr_manager_id`),
  ADD KEY `idx_jobs_status` (`status`),
  ADD KEY `idx_jobs_industry` (`industry`);

--
-- Indexes for table `job_skills`
--
ALTER TABLE `job_skills`
  ADD PRIMARY KEY (`job_id`,`skill_id`),
  ADD KEY `fk_js_skill` (`skill_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_notif_user` (`user_id`),
  ADD KEY `fk_notif_candidate` (`candidate_id`);

--
-- Indexes for table `ranking_results`
--
ALTER TABLE `ranking_results`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_rank_application` (`application_id`),
  ADD KEY `idx_rank_job_pos` (`job_id`,`ranking_position`);

--
-- Indexes for table `skills`
--
ALTER TABLE `skills`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_skills_normalized` (`normalized`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_users_email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `skills`
--
ALTER TABLE `skills`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `applications`
--
ALTER TABLE `applications`
  ADD CONSTRAINT `fk_app_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_app_cv` FOREIGN KEY (`cv_file_id`) REFERENCES `cv_files` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_app_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `candidate_skills`
--
ALTER TABLE `candidate_skills`
  ADD CONSTRAINT `fk_cs_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_cs_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `cv_files`
--
ALTER TABLE `cv_files`
  ADD CONSTRAINT `fk_cv_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `hr_managers`
--
ALTER TABLE `hr_managers`
  ADD CONSTRAINT `fk_hr_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `interviews`
--
ALTER TABLE `interviews`
  ADD CONSTRAINT `fk_interview_app` FOREIGN KEY (`application_id`) REFERENCES `applications` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_interview_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_interview_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `jobs`
--
ALTER TABLE `jobs`
  ADD CONSTRAINT `fk_jobs_hr` FOREIGN KEY (`hr_manager_id`) REFERENCES `hr_managers` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `job_skills`
--
ALTER TABLE `job_skills`
  ADD CONSTRAINT `fk_js_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_js_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `fk_notif_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_notif_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `ranking_results`
--
ALTER TABLE `ranking_results`
  ADD CONSTRAINT `fk_rank_app` FOREIGN KEY (`application_id`) REFERENCES `applications` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_rank_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
