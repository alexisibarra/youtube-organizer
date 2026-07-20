## PR Description

<!-- Describe the change and why it's needed -->

**Story/Issue:** [Link to story in planning artifacts or issue number]

**Change type:** 
- [ ] Feature implementation (user-facing behavior)
- [ ] Bug fix
- [ ] Test coverage
- [ ] Documentation
- [ ] Chore / refactor

---

## Testing Checklist

⚠️ **All PRs that implement a story must verify the items in [testing-checklist.md](../../Docs/MVPDefinition/05-development/testing-checklist.md).**

For **backend story implementation** (e.g., Story 2.1, 3.2, 5.1):

- [ ] I have read the acceptance criteria for this story in `_bmad-output/planning-artifacts/epics.md`
- [ ] I have identified the applicable service(s) from the [six critical backend services](../../Docs/MVPDefinition/05-development/testing-checklist.md#backend-6-critical-services)
- [ ] I have written **unit tests** (mocked dependencies) OR **integration tests** (real test DB) as specified in the checklist for this story
- [ ] Test names describe what is being tested (e.g., `describe('AuthService.register')`, `it('should throw ConflictException on duplicate email')`)
- [ ] I've verified tests pass locally: `pnpm exec nx run backend:test --coverage`
- [ ] Coverage for this service is at least 70% across all metrics (lines, statements, functions, branches)

For **frontend story implementation** (e.g., Story 2.4, 3.3, 5.2):

- [ ] I have read the acceptance criteria for this story in `_bmad-output/planning-artifacts/epics.md`
- [ ] I have identified the applicable component(s)/utility(ies) from the [critical frontend components](../../Docs/MVPDefinition/05-development/testing-checklist.md#frontend-critical-components--utilities)
- [ ] I have written **component tests** (React Testing Library with QueryClient mock) OR **utility tests** as specified in the checklist for this story
- [ ] Test names describe user interactions/data transformations (e.g., `it('displays error message on failed login')`, `it('calculates net worth correctly')`)
- [ ] I've verified tests pass locally: `pnpm exec nx run frontend:test --coverage`
- [ ] Coverage for this component/utility is at least 70% across all metrics
- [ ] All API calls are mocked (using jest.mock() or similar); no real API calls in tests

For **non-story PRs** (docs, chores, etc.):

- [ ] This is a non-story PR and test coverage is not required for this change, OR
- [ ] I have updated existing tests if my changes affect tested code

---

## CI & Coverage

✅ **CI will**:
- Run affected tests with coverage reporting
- Fail if coverage drops below 70% for critical services
- Upload coverage reports as artifacts
- Display coverage summary in this PR

📊 **Coverage report** will appear in the GitHub Actions summary after CI runs.

---

## Reviewer Checklist

- [ ] Tests match the story's acceptance criteria from the epics
- [ ] Mocked vs. real DB approach aligns with [unit vs integration guidance](../../Docs/MVPDefinition/05-development/testing-checklist.md#unit-vs-integration-tests)
- [ ] No monetary values are passed as JavaScript `number` (should be `string` or `Decimal`)
- [ ] Service layer uses `HttpException` subclasses; global filter handles wrapping
- [ ] DTOs use `class-validator` decorators (backend)
