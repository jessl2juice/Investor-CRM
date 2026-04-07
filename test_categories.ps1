# BetterMind CRM - Non-Destructive Category/Subcategory Test Suite
# All test objects are created and then deleted at the end.

$base = "http://localhost:8080"
$pass = 0
$fail = 0
$cleanup = @()  # Track IDs to clean up

function Test($name, $condition, $detail) {
    if ($condition) {
        Write-Host "  PASS  $name" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "  FAIL  $name  [$detail]" -ForegroundColor Red
        $script:fail++
    }
}

function Api($method, $path, $body) {
    $params = @{
        Uri = "$base/api$path"
        Method = $method
        Headers = @{Authorization = "Bearer $token"}
        ContentType = "application/json"
        UseBasicParsing = $true
    }
    if ($body) { $params.Body = [System.Text.Encoding]::UTF8.GetBytes($body) }
    try {
        $resp = Invoke-WebRequest @params
        $parsed = $null; try { $parsed = $resp.Content | ConvertFrom-Json } catch {}
        return @{ Status = [int]$resp.StatusCode; Body = $parsed; Raw = $resp.Content }
    } catch {
        $errBody = ""
        $code = 0
        try {
            $response = $_.Exception.Response
            $code = [int]$response.StatusCode
            $stream = $response.GetResponseStream()
            $ms = New-Object System.IO.MemoryStream
            $stream.CopyTo($ms)
            $ms.Position = 0
            $reader = New-Object System.IO.StreamReader($ms)
            $errBody = $reader.ReadToEnd()
            $reader.Close()
            $ms.Close()
            $stream.Close()
        } catch {}
        $parsed = $null; try { $parsed = $errBody | ConvertFrom-Json } catch {}
        return @{ Status = $code; Body = $parsed; Raw = $errBody }
    }
}

# ── 0. Auth ──────────────────────────────────────────────────────
Write-Host "`n========== AUTHENTICATION ==========" -ForegroundColor Cyan
$loginBody = '{"email":"jess@clinicianassist.ai","password":"Onelongpassword!"}'
$loginResp = Invoke-RestMethod -Uri "$base/api/login" -Method POST -ContentType "application/json" -Body $loginBody
$token = $loginResp.token
Test "Login succeeds" ($token.Length -gt 10) "No token returned"
Test "Login returns admin role" ($loginResp.role -eq "admin") "role=$($loginResp.role)"

# ── 1. Baseline snapshot ─────────────────────────────────────────
Write-Host "`n========== BASELINE SNAPSHOT ==========" -ForegroundColor Cyan
$stats = (Api "GET" "/stats").Body
$baseContacts = $stats.total_contacts
$baseInvestors = $stats.active_investors
$baseDeals = $stats.active_deals
$baseInteractions = $stats.total_interactions
$baseOrgs = $stats.total_organizations
Write-Host "  Contacts: $baseContacts | Active investors: $baseInvestors | Deals: $baseDeals | Interactions: $baseInteractions | Orgs: $baseOrgs"
Test "Baseline contacts > 0" ($baseContacts -gt 0) "total_contacts=$baseContacts"

# ── 2. GET /api/categories ───────────────────────────────────────
Write-Host "`n========== GET /api/categories ==========" -ForegroundColor Cyan
$r = Api "GET" "/categories"
Test "Status 200" ($r.Status -eq 200) "status=$($r.Status)"
$cats = $r.Body
Test "Returns 10 categories" ($cats.Count -eq 10) "count=$($cats.Count)"

$catNames = $cats | ForEach-Object { $_.name } | Sort-Object
$expected = @("advisor","google","investor","legislator","media","other","partner","team","university","vendor") | Sort-Object
Test "All expected category names present" (($catNames -join ",") -eq ($expected -join ",")) "got: $($catNames -join ',')"

$legislator = $cats | Where-Object { $_.name -eq "legislator" }
Test "Legislator category exists" ($null -ne $legislator) ""
Test "Legislator icon is not empty" ($legislator.icon.Length -gt 0) "icon=$($legislator.icon)"
Test "Legislator has 2 subcategories" ($legislator.subcategories.Count -eq 2) "count=$($legislator.subcategories.Count)"

$subNames = $legislator.subcategories | ForEach-Object { $_.name } | Sort-Object
Test "Legislator subcats are National, State" (($subNames -join ",") -eq "National,State") "got: $($subNames -join ',')"

$natl = $legislator.subcategories | Where-Object { $_.name -eq "National" }
Test "National display_name = 'National (Federal)'" ($natl.display_name -eq "National (Federal)") "display=$($natl.display_name)"

$st = $legislator.subcategories | Where-Object { $_.name -eq "State" }
Test "State display_name = 'State Legislature'" ($st.display_name -eq "State Legislature") "display=$($st.display_name)"

$investor = $cats | Where-Object { $_.name -eq "investor" }
Test "Investor has 22 subcategories" ($investor.subcategories.Count -eq 22) "count=$($investor.subcategories.Count)"
Test "Investor icon is not empty" ($investor.icon.Length -gt 0) "icon=$($investor.icon)"

$team = $cats | Where-Object { $_.name -eq "team" }
Test "Team has 3 subcategories (Co-Founder, Founder, Hire)" ($team.subcategories.Count -eq 3) "count=$($team.subcategories.Count)"

$advisor = $cats | Where-Object { $_.name -eq "advisor" }
Test "Advisor has 7 subcategories" ($advisor.subcategories.Count -eq 7) "count=$($advisor.subcategories.Count)"

$google = $cats | Where-Object { $_.name -eq "google" }
Test "Google has 4 subcategories" ($google.subcategories.Count -eq 4) "count=$($google.subcategories.Count)"

# ── 3. GET /api/categories/{id} ──────────────────────────────────
Write-Host "`n========== GET /api/categories/{id} ==========" -ForegroundColor Cyan
$r = Api "GET" "/categories/$($legislator.id)"
Test "Single category fetch returns 200" ($r.Status -eq 200) "status=$($r.Status)"
Test "Returns legislator by ID" ($r.Body.name -eq "legislator") "name=$($r.Body.name)"
Test "Includes subcategories" ($r.Body.subcategories.Count -eq 2) "count=$($r.Body.subcategories.Count)"

$r404 = Api "GET" "/categories/99999"
Test "Non-existent category returns 404" ($r404.Status -eq 404) "status=$($r404.Status)"

# ── 4. GET /api/subcategories ────────────────────────────────────
Write-Host "`n========== GET /api/subcategories ==========" -ForegroundColor Cyan
$r = Api "GET" "/subcategories"
Test "List all subcategories returns 200" ($r.Status -eq 200) "status=$($r.Status)"
$allSubs = $r.Body
Test "Total subcategories >= 40" ($allSubs.Count -ge 40) "count=$($allSubs.Count)"

$r = Api "GET" "/subcategories?category_id=$($legislator.id)"
Test "Filter by legislator category_id returns 2" ($r.Body.Count -eq 2) "count=$($r.Body.Count)"

$r = Api "GET" "/subcategories?category_id=$($investor.id)"
Test "Filter by investor category_id returns 22" ($r.Body.Count -eq 22) "count=$($r.Body.Count)"

# ── 5. POST /api/categories (create + cleanup) ──────────────────
Write-Host "`n========== POST /api/categories ==========" -ForegroundColor Cyan
$r = Api "POST" "/categories" '{"name":"zzz_test_cat","display_name":"ZZZ Test","icon":"T","sort_order":99}'
Test "Create new category returns 201" ($r.Status -eq 201) "status=$($r.Status)"
$testCatId = $r.Body.id
Test "New category has correct name" ($r.Body.name -eq "zzz_test_cat") "name=$($r.Body.name)"
Test "New category has correct icon" ($r.Body.icon -eq "T") "icon=$($r.Body.icon)"
$cleanup += @{type="category";id=$testCatId}

$rDup = Api "POST" "/categories" '{"name":"zzz_test_cat","display_name":"Dup"}'
Test "Duplicate category returns 409" ($rDup.Status -eq 409) "status=$($rDup.Status)"

$rBad = Api "POST" "/categories" '{"name":"","display_name":"Empty"}'
Test "Empty name returns 400" ($rBad.Status -eq 400) "status=$($rBad.Status)"

# ── 6. PUT /api/categories/{id} ─────────────────────────────────
Write-Host "`n========== PUT /api/categories/{id} ==========" -ForegroundColor Cyan
$r = Api "PUT" "/categories/$testCatId" '{"display_name":"ZZZ Updated","icon":"X"}'
Test "Update category returns 200" ($r.Status -eq 200) "status=$($r.Status)"
Test "Display name updated" ($r.Body.display_name -eq "ZZZ Updated") "display=$($r.Body.display_name)"
Test "Icon updated" ($r.Body.icon -eq "X") "icon=$($r.Body.icon)"

# ── 7. POST /api/subcategories ──────────────────────────────────
Write-Host "`n========== POST /api/subcategories ==========" -ForegroundColor Cyan
$subBody = @{category_id=$testCatId;name="ZZZ Sub One";display_name="ZZZ Sub Display";sort_order=1} | ConvertTo-Json
$r = Api "POST" "/subcategories" $subBody
Test "Create subcategory returns 201" ($r.Status -eq 201) "status=$($r.Status)"
$testSubId = $r.Body.id
Test "Subcategory name correct" ($r.Body.name -eq "ZZZ Sub One") "name=$($r.Body.name)"
$cleanup += @{type="subcategory";id=$testSubId}

$rBad = Api "POST" "/subcategories" '{"category_id":99999,"name":"orphan","display_name":"Orphan"}'
Test "Subcategory with invalid category_id returns 404" ($rBad.Status -eq 404) "status=$($rBad.Status)"

$rBad2 = Api "POST" "/subcategories" '{"name":"no_parent","display_name":"No Parent"}'
Test "Subcategory without category_id returns 400" ($rBad2.Status -eq 400) "status=$($rBad2.Status)"

# ── 8. PUT /api/subcategories/{id} ──────────────────────────────
Write-Host "`n========== PUT /api/subcategories/{id} ==========" -ForegroundColor Cyan
$r = Api "PUT" "/subcategories/$testSubId" '{"display_name":"ZZZ Sub Updated"}'
Test "Update subcategory returns 200" ($r.Status -eq 200) "status=$($r.Status)"
Test "Subcategory display_name updated" ($r.Body.display_name -eq "ZZZ Sub Updated") "display=$($r.Body.display_name)"

# ── 9. Contact creation with legislator ─────────────────────────
Write-Host "`n========== CONTACT + LEGISLATOR CATEGORY ==========" -ForegroundColor Cyan
$r = Api "POST" "/contacts" '{"first_name":"ZZZ_Test","last_name":"Legislator_State","category":"legislator","subcategory":"State","status":"active"}'
Test "Create legislator+State contact returns 201" ($r.Status -eq 201) "status=$($r.Status)"
$testContactId1 = $r.Body.id
$cleanup += @{type="contact";id=$testContactId1}

$r = Api "POST" "/contacts" '{"first_name":"ZZZ_Test","last_name":"Legislator_Natl","category":"legislator","subcategory":"National","status":"active"}'
Test "Create legislator+National contact returns 201" ($r.Status -eq 201) "status=$($r.Status)"
$testContactId2 = $r.Body.id
$cleanup += @{type="contact";id=$testContactId2}

# Verify the created contacts
$r = Api "GET" "/contacts/$testContactId1"
Test "Fetched contact has category=legislator" ($r.Body.category -eq "legislator") "category=$($r.Body.category)"
Test "Fetched contact has subcategory=State" ($r.Body.subcategory -eq "State") "subcategory=$($r.Body.subcategory)"

$r = Api "GET" "/contacts/$testContactId2"
Test "National contact has subcategory=National" ($r.Body.subcategory -eq "National") "subcategory=$($r.Body.subcategory)"

# Create contact with no subcategory (should work)
$r = Api "POST" "/contacts" '{"first_name":"ZZZ_Test","last_name":"Legislator_NoSub","category":"legislator","status":"active"}'
Test "Create legislator without subcategory returns 201" ($r.Status -eq 201) "status=$($r.Status)"
$testContactId3 = $r.Body.id
$cleanup += @{type="contact";id=$testContactId3}

# ── 10. Validation: invalid category ────────────────────────────
Write-Host "`n========== VALIDATION: INVALID CATEGORY ==========" -ForegroundColor Cyan
$r = Api "POST" "/contacts" '{"first_name":"Bad","category":"fakecategory","status":"active"}'
Test "Invalid category returns 422" ($r.Status -eq 422) "status=$($r.Status)"
Test "Error message lists valid categories" ($r.Raw -match "Valid categories:") "body=$($r.Raw)"
Test "Error message mentions 'legislator'" ($r.Raw -match "legislator") "body=$($r.Raw)"

# ── 11. Validation: invalid subcategory ──────────────────────────
Write-Host "`n========== VALIDATION: INVALID SUBCATEGORY ==========" -ForegroundColor Cyan
$r = Api "POST" "/contacts" '{"first_name":"Bad","category":"legislator","subcategory":"County","status":"active"}'
Test "Invalid subcategory returns 422" ($r.Status -eq 422) "status=$($r.Status)"
Test "Error lists valid subcategories" ($r.Raw -match "Valid subcategories:") "body=$($r.Raw)"

# Wrong parent: "Seed VC" belongs to investor, not legislator
$r = Api "POST" "/contacts" '{"first_name":"Bad","category":"legislator","subcategory":"Seed VC","status":"active"}'
Test "Cross-category subcategory returns 422" ($r.Status -eq 422) "status=$($r.Status)"

# Category with no subcategories defined: "media" has none → any subcategory should fail
$r = Api "POST" "/contacts" '{"first_name":"Bad","category":"media","subcategory":"TV","status":"active"}'
Test "Subcategory for category with none defined returns 422" ($r.Status -eq 422) "status=$($r.Status)"
Test "Error mentions no defined subcategories" ($r.Raw -match "no defined subcategories") "body=$($r.Raw)"

# -- 12. PUT /api/contacts/{id} - update category
Write-Host "`n========== PUT /api/contacts/{id} - CATEGORY UPDATE ==========" -ForegroundColor Cyan
$updateBody = @{category="investor";subcategory="Seed VC"} | ConvertTo-Json
$r = Api "PUT" "/contacts/$testContactId3" $updateBody
Test "Update contact category to investor+Seed VC returns 200" ($r.Status -eq 200) "status=$($r.Status)"
Test "Updated category = investor" ($r.Body.category -eq "investor") "category=$($r.Body.category)"
Test "Updated subcategory = Seed VC" ($r.Body.subcategory -eq "Seed VC") "subcategory=$($r.Body.subcategory)"

# Update with invalid category
$badCatBody = @{category="nope"} | ConvertTo-Json
$r = Api "PUT" "/contacts/$testContactId3" $badCatBody
Test "Update with invalid category returns 422" ($r.Status -eq 422) "status=$($r.Status)"

# Update subcategory only (wrong parent for current category)
$wrongSubBody = @{subcategory="State"} | ConvertTo-Json
$r = Api "PUT" "/contacts/$testContactId3" $wrongSubBody
Test "Update subcategory to wrong parent returns 422" ($r.Status -eq 422) "status=$($r.Status)"

# Revert back to legislator for cleanup clarity
$revertBody = @{category="legislator"} | ConvertTo-Json
$null = Api "PUT" "/contacts/$testContactId3" $revertBody

# ── 13. PUT /api/bulk/contacts ───────────────────────────────────
Write-Host "`n========== PUT /api/bulk/contacts ==========" -ForegroundColor Cyan
$bulkBody = @{contact_ids=@($testContactId1,$testContactId2);category="legislator"} | ConvertTo-Json
$r = Api "PUT" "/bulk/contacts" $bulkBody
Test "Bulk update with valid category returns 200" ($r.Status -eq 200) "status=$($r.Status)"
Test "Bulk update affected 2 rows" ($r.Body.updated -eq 2) "updated=$($r.Body.updated)"

$bulkBad = @{contact_ids=@($testContactId1);category="nope"} | ConvertTo-Json
$r = Api "PUT" "/bulk/contacts" $bulkBad
Test "Bulk update with invalid category returns 422" ($r.Status -eq 422) "status=$($r.Status)"

# ── 14. Existing categories still work ───────────────────────────
Write-Host "`n========== EXISTING CATEGORIES STILL WORK ==========" -ForegroundColor Cyan
foreach ($cat in @("investor","google","team","advisor","partner","vendor","university","media","other")) {
    $r = Api "GET" "/contacts?category=$cat&limit=1"
    $count = $r.Body.Count
    # Some categories may have 0 contacts in prod data, that's fine — just ensure no errors
    Test "GET /contacts?category=$cat returns 200" ($r.Status -eq 200) "status=$($r.Status)"
}

# Spot-check a known investor contact still has correct data
$r = Api "GET" "/contacts?category=investor&limit=1"
if ($r.Body.Count -gt 0) {
    $c = $r.Body[0]
    Test "Existing investor contact has category=investor" ($c.category -eq "investor") "category=$($c.category)"
    Test "Existing investor contact has a first_name" ($c.first_name.Length -gt 0) "first_name=$($c.first_name)"
}

# ── 15. DELETE protection ────────────────────────────────────────
Write-Host "`n========== DELETE PROTECTION (in-use) ==========" -ForegroundColor Cyan
$investorCat = $cats | Where-Object { $_.name -eq "investor" }
$r = Api "DELETE" "/categories/$($investorCat.id)"
Test "Cannot delete investor category (contacts use it) → 409" ($r.Status -eq 409) "status=$($r.Status)"

# ── 16. Final baseline comparison ────────────────────────────────
Write-Host "`n========== CLEANUP ==========" -ForegroundColor Cyan
# Delete test contacts first
foreach ($item in ($cleanup | Where-Object { $_.type -eq "contact" })) {
    $r = Api "DELETE" "/contacts/$($item.id)"
    Test "Cleanup: delete test contact $($item.id)" ($r.Status -eq 200) "status=$($r.Status)"
}
# Delete test subcategories
foreach ($item in ($cleanup | Where-Object { $_.type -eq "subcategory" })) {
    $r = Api "DELETE" "/subcategories/$($item.id)"
    Test "Cleanup: delete test subcategory $($item.id)" ($r.Status -eq 200) "status=$($r.Status)"
}
# Delete test categories
foreach ($item in ($cleanup | Where-Object { $_.type -eq "category" })) {
    $r = Api "DELETE" "/categories/$($item.id)"
    Test "Cleanup: delete test category $($item.id)" ($r.Status -eq 200) "status=$($r.Status)"
}

Write-Host "`n========== POST-CLEANUP VERIFICATION ==========" -ForegroundColor Cyan
$statsAfter = (Api "GET" "/stats").Body
Test "Contact count unchanged ($baseContacts)" ($statsAfter.total_contacts -eq $baseContacts) "before=$baseContacts after=$($statsAfter.total_contacts)"
Test "Active investors unchanged ($baseInvestors)" ($statsAfter.active_investors -eq $baseInvestors) "before=$baseInvestors after=$($statsAfter.active_investors)"
Test "Deals unchanged ($baseDeals)" ($statsAfter.active_deals -eq $baseDeals) "before=$baseDeals after=$($statsAfter.active_deals)"
Test "Interactions unchanged ($baseInteractions)" ($statsAfter.total_interactions -eq $baseInteractions) "before=$baseInteractions after=$($statsAfter.total_interactions)"
Test "Orgs unchanged ($baseOrgs)" ($statsAfter.total_organizations -eq $baseOrgs) "before=$baseOrgs after=$($statsAfter.total_organizations)"

$catsAfter = (Api "GET" "/categories").Body
Test "Category count still 10" ($catsAfter.Count -eq 10) "count=$($catsAfter.Count)"

# ── SUMMARY ──────────────────────────────────────────────────────
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "  PASSED: $pass" -ForegroundColor Green
Write-Host "  FAILED: $fail" -ForegroundColor $(if ($fail -gt 0) { "Red" } else { "Green" })
Write-Host "==========================================" -ForegroundColor Cyan
