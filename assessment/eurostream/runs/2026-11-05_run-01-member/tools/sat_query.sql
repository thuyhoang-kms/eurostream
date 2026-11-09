SELECT b.check_id, c.score, c.additional_details, c.run_id, c.check_time
FROM `sat`.security_analysis.security_checks c JOIN `sat`.security_analysis.security_best_practices b ON c.id = b.id
WHERE c.workspaceid = '7474650345400041'
  AND c.run_id = (SELECT max(run_id) FROM `sat`.security_analysis.security_checks WHERE workspaceid = '7474650345400041')
