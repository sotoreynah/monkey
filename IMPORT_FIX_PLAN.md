# Import Source Selection Fix

## Problem
- Checking 1569 and Credit Card 6032 have identical CSV column structures
- Auto-detection assigns wrong source (transactions from 1569 getting marked as 6032)
- No way for user to manually override source selection

## Impact
- Incorrect source assignment affects reporting and analysis
- Example: $10,500 Robinhood transactions from checking (1569) marked as credit card (6032)

## Solution: Add Manual Source Selection

### Backend Changes

#### 1. Update `/api/imports/upload` endpoint
Add optional `source_id` parameter:
```python
@router.post("/upload", response_model=ImportResponse)
async def upload_csv(
    file: UploadFile = File(...),
    source_id: int | None = Form(None),  # NEW: Manual source override
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
```

#### 2. Update `ImportService.import_csv()` method
Add source_id parameter:
```python
def import_csv(
    self, 
    file_path: str, 
    file_hash: str, 
    filename: str,
    source_id: int | None = None  # NEW
) -> dict:
    if source_id:
        # Use manually selected source
        source = self.db.query(TransactionSource).get(source_id)
        if not source:
            raise ValueError(f"Source ID {source_id} not found")
        parser = self._get_parser_for_source(source)
    else:
        # Auto-detect (existing behavior)
        parser = self.detect_parser(file_path)
        source = self.get_or_create_source(parser)
```

#### 3. Add `_get_parser_for_source()` helper
Map source to appropriate parser:
```python
def _get_parser_for_source(self, source: TransactionSource):
    """Get parser based on source name"""
    parser_map = {
        "Credit Card 6032": CreditCard6032Parser,
        "Checking 1569": Checking1569Parser,
        "Apple Card": AppleCardParser,
        "AMEX": AmexParser,
    }
    parser_cls = parser_map.get(source.name)
    if not parser_cls:
        raise ValueError(f"No parser found for source: {source.name}")
    return parser_cls()
```

### Frontend Changes

#### 1. Add GET `/api/transaction-sources` endpoint
List available sources for dropdown:
```python
@router.get("/sources")
def list_sources(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    sources = db.query(TransactionSource).filter(
        TransactionSource.active == True
    ).all()
    return [{"id": s.id, "name": s.name, "type": s.type} for s in sources]
```

#### 2. Update Import UI (frontend/src/pages/Import.jsx)
Add source dropdown ABOVE file upload:
```jsx
<div className="mb-4">
  <label className="block text-sm font-medium mb-2">
    Transaction Source
  </label>
  <select 
    value={selectedSource} 
    onChange={(e) => setSelectedSource(e.target.value)}
    className="w-full border rounded px-3 py-2"
  >
    <option value="">Auto-detect (may be inaccurate)</option>
    {sources.map(s => (
      <option key={s.id} value={s.id}>
        {s.name} ({s.type})
      </option>
    ))}
  </select>
  <p className="text-xs text-gray-500 mt-1">
    ⚠️ Manual selection recommended to avoid mis-categorization
  </p>
</div>
```

#### 3. Update form submission
Include source_id in FormData:
```jsx
const formData = new FormData();
formData.append('file', file);
if (selectedSource) {
  formData.append('source_id', selectedSource);
}
```

## Migration: Fix Existing Data

### Script to reassign transactions from 6032 → 1569
```python
# fix_robinhood_source.py
# Find all WEB AUTHORIZED PMT ROBINHOOD from 6032
# that should be from 1569 (checking account)

UPDATE transactions
SET source_id = (SELECT id FROM transaction_sources WHERE name = 'Checking 1569')
WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Credit Card 6032')
  AND description LIKE '%WEB AUTHORIZED PMT ROBINHOOD%'
```

### More comprehensive fix
Review ALL transactions from 6032 to check for other mis-assignments:
- ROBINHOOD payments
- AMEX payments  
- APPLECARD payments
- Any other "WEB AUTHORIZED PMT" that should be from checking

## Implementation Priority

1. **HIGH** - Backend source_id parameter (quick fix)
2. **HIGH** - Frontend source dropdown
3. **MEDIUM** - Data migration script
4. **LOW** - Improve auto-detection logic (long-term)

## Testing

1. Upload same CSV with manual source selection → verify correct assignment
2. Upload CSV with auto-detect → show warning if ambiguous
3. Verify existing data after migration

---

Ready to implement?
