# Evaluate actual reviews

1. Install Codzee for this repository before opening the three PRs. Open ready
   PRs, not drafts, unless the product explicitly supports draft reviews.
2. Record branch/head SHA, opening time, review start/completion time, and the
   GitHub review/check/comment links. Distinguish setup delays from review time.
3. Read every finding. Reproduce it with a test or API request before accepting
   it. Note correctness, severity, actionability, and awareness of repo context.
4. Test a justified fix on the same branch and push it. Observe whether the next
   review recognizes the fix, repeats resolved feedback, or reviews an old SHA.
5. Keep an honest record of wrong or redundant comments and product UX issues.
   A missing comment is not automatically a missed bug: give a concrete defect
   and reproducer, and distinguish changed code from unrelated baseline backlog.
6. Open all three PRs against main before merging; leave them and their comments
   publicly accessible. If you merge, run the combined test suite afterwards.
7. Write feedback only from observed evidence. Submit the Google Form after the
   reviews run and you have checked repository access in a signed-out window.

| Area | Reproducible scenario | Expected behavior |
| --- | --- | --- |
| Validation | Short title / new past date | 400 with field error, no invalid write |
| PATCH | Overdue task, update only status | Update succeeds, old date preserved |
| Isolation | Alice GET/PATCH/PUT/DELETE Bob's ID | 404; Bob's task unchanged after PR 2 |
| Ownership | Alice sends Bob's ID as owner | Server retains Alice as owner |
| Pagination | 25 tasks, default first page | Count 25, results 20, next page exists |
| Bounds | page_size=1000 with 105 tasks | Results capped at 100 |
| Stability | Equal timestamps across pages | No duplicate or skipped task IDs in a static dataset |
| Queries | Serialize 1 and 20 task owners | Constant query count with select_related |
| Composition | Merge all three locally | All tests pass; filtering preserves isolation |

Suggestions to consider only if your experience supports them: review progress
visibility, reproducible findings, resolved-comment tracking, repository setup
guidance, framework-specific context, and confidence/severity explanations.
Do not present these hypotheses as bugs you observed.
