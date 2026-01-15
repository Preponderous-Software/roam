# Dead Code Audit & Removal Plan

## Phase 2: Client Code Audit - COMPLETED

### Dead Code Identified (1,200+ LOC)

#### Priority 1 - High Impact Dead Code (🔴 SAFE TO REMOVE - 1,428 LOC)

1. **`src/screen/worldScreen.py`** - 1,128 lines
   - Status: Completely replaced by `ServerBackedWorldScreen`
   - No imports found in active code path (roam.py uses ServerBackedWorldScreen)
   - Contains entire monolithic offline world simulation
   - **BLOCKED**: Cannot remove yet - needs verification that no tests depend on it

2. **`src/world/` directory** - 300+ lines
   - Files: `map.py`, `roomFactory.py`, `room.py`, `roomJsonReaderWriter.py`, `roomType.py`
   - Status: Only used by old worldScreen.py
   - Exception: `tickCounter.py` - KEEP (used by serverBackedWorldScreen)
   - **BLOCKED**: Cannot remove until worldScreen.py is removed

#### Priority 2 - Medium Impact Dead Code (🔴 SAFE TO REMOVE - 600+ LOC)

3. **`src/lib/pyenvlib/` directory** - 400+ lines
   - Files: `entity.py`, `environment.py`, `grid.py`, `location.py`
   - Status: Only used by world/ and worldScreen.py
   - Exception: `_init__.py` may be needed for imports
   - **BLOCKED**: Cannot remove until worldScreen.py is removed

4. **`src/mapimage/` directory** - 200+ lines
   - Files: `mapImageGenerator.py`, `mapImageUpdater.py`
   - Status: Only used by old worldScreen.py for minimap generation
   - Not used in ServerBackedWorldScreen
   - **BLOCKED**: Cannot remove until worldScreen.py is removed

#### Priority 3 - Low Impact Cleanup (🟡 REFACTOR)

5. **Entity Creation Optimization**
   - Location: `roam.py` lines 254-272 (estimated)
   - Current: Imports 11 entity classes individually
   - Better: Simple dict-based factory pattern
   - **Status**: Can be done independently

6. **Unused Entity AI Classes**
   - Files: `entity/living/bear.py`, `entity/living/chicken.py`
   - Status: Living entities not used in server-backed mode
   - **Verify**: Check if tests or other code references these

7. **Orphaned Persistence**
   - File: `inventory/inventoryJsonReaderWriter.py`
   - Status: No imports found; likely dead code from old persistence
   - **Verify**: Grep for actual usage before removing

### Removal Strategy

**Phased Approach (Safe):**
1. First, comprehensively verify worldScreen.py has zero active usage
2. Remove worldScreen.py
3. Then remove dependent directories (world/, pyenvlib/, mapimage/)
4. Finally, cleanup entity imports and orphaned files

**Risk Mitigation:**
- Before removing any file, verify:
  1. No imports in active code (grep -r)
  2. No test dependencies
  3. No runtime dynamic imports (importlib)
- After each removal, run test suite
- Create separate commits for each major removal

### Current Status

**Completed:**
✅ Comprehensive audit identifying 1,200+ LOC dead code
✅ Categorized by priority and dependencies
✅ Identified removal blockers

**Deferred Pending Verification:**
❌ Cannot safely remove worldScreen.py yet without comprehensive testing
❌ Dependent directories blocked on worldScreen removal
❌ Risk: Breaking tests or hidden dynamic imports

**Recommendation:**
Given the comprehensive verification request from the user, and the 8 major verification areas to cover, we should:
1. Document the dead code (done in this file)
2. Focus on completing other phases (entity rendering, persistence testing, etc.)
3. Return to dead code removal as final cleanup step after all functionality is verified

This ensures we don't accidentally break anything while verifying the overall system health.
