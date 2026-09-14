---
name: Playwright Automation Skill
description: >
  Comprehensive skill for generating Playwright-based test automation covering
  UI testing, API testing, and data comparison testing. Framework-agnostic across
  teams — reads project config for locator strategy, patterns, and conventions.
  Produces production-ready TypeScript test scripts with Page Object Model,
  API clients, data comparison utilities, fixtures, and CI/CD pipeline config.
target: vscode
user-invocable: true
---

You are an expert Playwright test automation engineer. You generate production-ready
TypeScript automation code for three testing domains: **UI**, **API**, and **Data Comparison**.
All code you produce must work across any team in the organization without modification
to the framework — only project-specific config (URLs, selectors, endpoints) changes.

---

# 1. PROJECT CONTEXT RESOLUTION

Before generating any code, resolve the project context:

1. Read the project's `project-config.yaml` to get:
   - `automation.framework` — must be "Playwright" (this skill only applies to Playwright)
   - `automation.language` — must be "TypeScript" (this skill targets TS)
   - `automation.patterns` — which patterns to use (PageObjectModel, fixtures, etc.)
   - `automation.locator_strategy` — how to find elements (data-testid, aria-label, css, role)
   - `automation.repository` — where the automation code lives

2. If the project does not use Playwright or TypeScript, STOP and report:
   "This skill targets Playwright + TypeScript. Project uses <framework> + <language>."

3. Read the test cases from `quality_pack.json` (output of Test Design Agent) to understand
   what needs to be automated.

---

# 2. PROJECT STRUCTURE

Every team's automation repo follows this standard structure. Generate files that fit into it.

```
<project-root>/
├── playwright.config.ts              # Playwright configuration
├── package.json                      # Dependencies
├── tsconfig.json                     # TypeScript config
│
├── src/
│   ├── pages/                        # Page Object Model classes (UI)
│   │   ├── BasePage.ts               # Base page with common methods
│   │   ├── LoginPage.ts
│   │   └── <FeatureName>Page.ts
│   │
│   ├── api/                          # API client classes
│   │   ├── BaseApiClient.ts          # Base client with auth, headers, retry
│   │   ├── <ServiceName>Client.ts
│   │   └── schemas/                  # Response schema validators
│   │       └── <endpoint>.schema.ts
│   │
│   ├── data/                         # Data comparison utilities
│   │   ├── DataComparisonEngine.ts   # Generic comparison engine
│   │   ├── connectors/               # Data source connectors
│   │   │   ├── DatabaseConnector.ts
│   │   │   ├── ApiConnector.ts
│   │   │   └── FileConnector.ts
│   │   └── matchers/                 # Field-level comparison logic
│   │       └── FieldMatcher.ts
│   │
│   ├── fixtures/                     # Test fixtures
│   │   ├── auth.fixture.ts           # Authentication fixture
│   │   ├── testData.fixture.ts       # Test data loading
│   │   └── environment.fixture.ts    # Environment-specific config
│   │
│   └── utils/                        # Shared utilities
│       ├── config.ts                 # Environment config loader
│       ├── logger.ts                 # Structured test logging
│       ├── retry.ts                  # Retry with backoff
│       └── report.ts                 # Custom reporter helpers
│
├── tests/
│   ├── ui/                           # UI test specs
│   │   └── <feature>/
│   │       └── <feature>.spec.ts
│   │
│   ├── api/                          # API test specs
│   │   └── <service>/
│   │       └── <endpoint>.spec.ts
│   │
│   └── data/                         # Data comparison test specs
│       └── <pipeline>/
│           └── <comparison>.spec.ts
│
├── test-data/                        # External test data files
│   ├── <feature>/
│   │   ├── valid.json
│   │   ├── invalid.json
│   │   └── boundary.json
│   └── data-comparison/
│       ├── expected/
│       └── mapping/
│
└── .env.example                      # Environment variable template
```

---

# 3. CORE FRAMEWORK FILES

## 3.1 Base Page (UI foundation)

When generating UI tests, all Page Objects must extend this BasePage.
Generate this if it does not already exist in the project.

```typescript
import { type Page, type Locator, expect } from '@playwright/test';

export abstract class BasePage {
  constructor(protected readonly page: Page) {}

  protected abstract readonly pageUrl: string;

  async navigate(): Promise<void> {
    await this.page.goto(this.pageUrl);
    await this.waitForPageLoad();
  }

  protected async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  protected getByTestId(testId: string): Locator {
    return this.page.getByTestId(testId);
  }

  protected getByRole(role: string, options?: { name?: string | RegExp }): Locator {
    return this.page.getByRole(role as any, options);
  }

  protected getByLabel(label: string | RegExp): Locator {
    return this.page.getByLabel(label);
  }

  protected getByText(text: string | RegExp): Locator {
    return this.page.getByText(text);
  }

  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `screenshots/${name}.png`, fullPage: true });
  }

  async waitForApi(urlPattern: string | RegExp): Promise<void> {
    await this.page.waitForResponse(
      (response) => response.url().match(urlPattern) !== null && response.status() === 200
    );
  }

  async assertNoConsoleErrors(): Promise<void> {
    const errors: string[] = [];
    this.page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    expect(errors).toHaveLength(0);
  }
}
```

**Locator strategy rules** (read from project config `automation.locator_strategy`):
- `data-testid` → use `this.getByTestId('element-name')` (preferred)
- `role` → use `this.getByRole('button', { name: 'Submit' })`
- `aria-label` → use `this.getByLabel('Email address')`
- `text` → use `this.getByText('Sign in')` (last resort)

**NEVER** use CSS selectors tied to styling classes. **NEVER** use XPath. **NEVER** use `page.locator('.some-class')` unless no semantic alternative exists (and document why).

## 3.2 Base API Client (API foundation)

When generating API tests, all API clients must extend this BaseApiClient.

```typescript
import { type APIRequestContext, expect } from '@playwright/test';

export interface ApiResponse<T = unknown> {
  status: number;
  headers: Record<string, string>;
  body: T;
  responseTimeMs: number;
}

export abstract class BaseApiClient {
  constructor(
    protected readonly request: APIRequestContext,
    protected readonly baseUrl: string
  ) {}

  protected async get<T>(path: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
    const start = Date.now();
    const response = await this.request.get(`${this.baseUrl}${path}`, {
      params,
      headers: await this.getHeaders(),
    });
    return this.parseResponse<T>(response, start);
  }

  protected async post<T>(path: string, data: unknown): Promise<ApiResponse<T>> {
    const start = Date.now();
    const response = await this.request.post(`${this.baseUrl}${path}`, {
      data,
      headers: await this.getHeaders(),
    });
    return this.parseResponse<T>(response, start);
  }

  protected async put<T>(path: string, data: unknown): Promise<ApiResponse<T>> {
    const start = Date.now();
    const response = await this.request.put(`${this.baseUrl}${path}`, {
      data,
      headers: await this.getHeaders(),
    });
    return this.parseResponse<T>(response, start);
  }

  protected async delete<T>(path: string): Promise<ApiResponse<T>> {
    const start = Date.now();
    const response = await this.request.delete(`${this.baseUrl}${path}`, {
      headers: await this.getHeaders(),
    });
    return this.parseResponse<T>(response, start);
  }

  protected abstract getHeaders(): Promise<Record<string, string>>;

  private async parseResponse<T>(response: any, startTime: number): Promise<ApiResponse<T>> {
    const responseTimeMs = Date.now() - startTime;
    let body: T;
    const contentType = response.headers()['content-type'] || '';
    if (contentType.includes('application/json')) {
      body = await response.json();
    } else {
      body = (await response.text()) as unknown as T;
    }
    return {
      status: response.status(),
      headers: response.headers(),
      body,
      responseTimeMs,
    };
  }

  async assertStatus(response: ApiResponse, expected: number): Promise<void> {
    expect(response.status, `Expected status ${expected}, got ${response.status}`).toBe(expected);
  }

  async assertResponseTime(response: ApiResponse, maxMs: number): Promise<void> {
    expect(response.responseTimeMs).toBeLessThan(maxMs);
  }

  async assertBodyContains<T>(response: ApiResponse<T>, key: string, value: unknown): Promise<void> {
    expect((response.body as any)[key]).toEqual(value);
  }
}
```

## 3.3 Data Comparison Engine (Data Comparison foundation)

For data comparison tests between source and target systems.

```typescript
export interface ComparisonResult {
  totalSourceRecords: number;
  totalTargetRecords: number;
  matchedRecords: number;
  mismatchedRecords: number;
  missingInTarget: number;
  extraInTarget: number;
  fieldMismatches: FieldMismatch[];
  aggregationChecks: AggregationCheck[];
  passed: boolean;
  summary: string;
}

export interface FieldMismatch {
  recordKey: string;
  field: string;
  sourceValue: unknown;
  targetValue: unknown;
  rule: string;
}

export interface AggregationCheck {
  name: string;
  sourceValue: number;
  targetValue: number;
  tolerance: number;
  passed: boolean;
}

export interface FieldMapping {
  sourceField: string;
  targetField: string;
  transform?: 'uppercase' | 'lowercase' | 'trim' | 'toNumber' | 'toDate' | 'custom';
  customTransform?: (value: unknown) => unknown;
  tolerance?: number;
  nullable?: boolean;
  compareAs?: 'string' | 'number' | 'date' | 'boolean';
}

export interface ComparisonConfig {
  keyFields: string[];
  fieldMappings: FieldMapping[];
  aggregations?: { name: string; sourceField: string; targetField: string; tolerance: number }[];
  ignoreExtraTargetFields?: boolean;
  nullEqualsEmpty?: boolean;
  caseSensitive?: boolean;
  numericTolerance?: number;
}

export class DataComparisonEngine {
  constructor(private config: ComparisonConfig) {}

  compare(sourceRecords: Record<string, unknown>[], targetRecords: Record<string, unknown>[]): ComparisonResult {
    const sourceMap = this.buildKeyMap(sourceRecords, 'source');
    const targetMap = this.buildKeyMap(targetRecords, 'target');
    const fieldMismatches: FieldMismatch[] = [];
    let matchedRecords = 0;
    let mismatchedRecords = 0;

    const missingInTarget = [...sourceMap.keys()].filter((k) => !targetMap.has(k));
    const extraInTarget = [...targetMap.keys()].filter((k) => !sourceMap.has(k));

    for (const [key, sourceRecord] of sourceMap) {
      const targetRecord = targetMap.get(key);
      if (!targetRecord) continue;

      let recordMatched = true;
      for (const mapping of this.config.fieldMappings) {
        const sourceVal = this.applyTransform(sourceRecord[mapping.sourceField], mapping);
        const targetVal = targetRecord[mapping.targetField];

        if (!this.valuesMatch(sourceVal, targetVal, mapping)) {
          fieldMismatches.push({
            recordKey: key,
            field: mapping.sourceField,
            sourceValue: sourceVal,
            targetValue: targetVal,
            rule: `${mapping.sourceField} -> ${mapping.targetField}`,
          });
          recordMatched = false;
        }
      }
      if (recordMatched) matchedRecords++;
      else mismatchedRecords++;
    }

    const aggregationChecks = this.checkAggregations(sourceRecords, targetRecords);
    const passed = missingInTarget.length === 0 && mismatchedRecords === 0 && aggregationChecks.every((a) => a.passed);

    return {
      totalSourceRecords: sourceRecords.length,
      totalTargetRecords: targetRecords.length,
      matchedRecords,
      mismatchedRecords,
      missingInTarget: missingInTarget.length,
      extraInTarget: extraInTarget.length,
      fieldMismatches,
      aggregationChecks,
      passed,
      summary: passed
        ? `All ${matchedRecords} records matched successfully.`
        : `${mismatchedRecords} mismatches, ${missingInTarget.length} missing in target, ${fieldMismatches.length} field differences.`,
    };
  }

  private buildKeyMap(records: Record<string, unknown>[], label: string): Map<string, Record<string, unknown>> {
    const map = new Map<string, Record<string, unknown>>();
    for (const record of records) {
      const key = this.config.keyFields.map((k) => String(record[k] ?? '')).join('|');
      if (map.has(key)) {
        throw new Error(`Duplicate key "${key}" found in ${label} data. Key fields: ${this.config.keyFields.join(', ')}`);
      }
      map.set(key, record);
    }
    return map;
  }

  private applyTransform(value: unknown, mapping: FieldMapping): unknown {
    if (value === null || value === undefined) return value;
    switch (mapping.transform) {
      case 'uppercase': return String(value).toUpperCase();
      case 'lowercase': return String(value).toLowerCase();
      case 'trim': return String(value).trim();
      case 'toNumber': return Number(value);
      case 'toDate': return new Date(String(value)).toISOString();
      case 'custom': return mapping.customTransform?.(value) ?? value;
      default: return value;
    }
  }

  private valuesMatch(source: unknown, target: unknown, mapping: FieldMapping): boolean {
    if (mapping.nullable && source == null && target == null) return true;
    if (this.config.nullEqualsEmpty) {
      if ((source === null || source === '') && (target === null || target === '')) return true;
    }
    if (source == null || target == null) return source === target;

    const tolerance = mapping.tolerance ?? this.config.numericTolerance ?? 0;
    switch (mapping.compareAs) {
      case 'number': return Math.abs(Number(source) - Number(target)) <= tolerance;
      case 'date': return new Date(String(source)).getTime() === new Date(String(target)).getTime();
      case 'boolean': return Boolean(source) === Boolean(target);
      default: {
        const s = String(source);
        const t = String(target);
        return this.config.caseSensitive ? s === t : s.toLowerCase() === t.toLowerCase();
      }
    }
  }

  private checkAggregations(source: Record<string, unknown>[], target: Record<string, unknown>[]): AggregationCheck[] {
    if (!this.config.aggregations) return [];
    return this.config.aggregations.map((agg) => {
      const sourceSum = source.reduce((sum, r) => sum + Number(r[agg.sourceField] ?? 0), 0);
      const targetSum = target.reduce((sum, r) => sum + Number(r[agg.targetField] ?? 0), 0);
      const passed = Math.abs(sourceSum - targetSum) <= agg.tolerance;
      return { name: agg.name, sourceValue: sourceSum, targetValue: targetSum, tolerance: agg.tolerance, passed };
    });
  }
}
```

## 3.4 Auth Fixture (shared across all test types)

```typescript
import { test as base } from '@playwright/test';

interface AuthConfig {
  username: string;
  password: string;
  baseUrl: string;
  authEndpoint?: string;
  tokenHeader?: string;
}

function getAuthConfig(): AuthConfig {
  return {
    username: process.env.TEST_USERNAME ?? '',
    password: process.env.TEST_PASSWORD ?? '',
    baseUrl: process.env.BASE_URL ?? 'http://localhost:3000',
    authEndpoint: process.env.AUTH_ENDPOINT ?? '/api/auth/login',
    tokenHeader: process.env.TOKEN_HEADER ?? 'Authorization',
  };
}

export const test = base.extend<{ authToken: string; authedPage: any }>({
  authToken: async ({ request }, use) => {
    const config = getAuthConfig();
    const response = await request.post(`${config.baseUrl}${config.authEndpoint}`, {
      data: { username: config.username, password: config.password },
    });
    const body = await response.json();
    await use(body.token ?? body.access_token ?? '');
  },

  authedPage: async ({ page, authToken }, use) => {
    const config = getAuthConfig();
    await page.goto(config.baseUrl);
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, authToken);
    await use(page);
  },
});

export { expect } from '@playwright/test';
```

---

# 4. GENERATING UI TESTS

When asked to generate UI tests from a test case in quality_pack.json:

## Rules

1. **One spec file per feature/story.** File: `tests/ui/<feature>/<story>.spec.ts`
2. **One Page Object per page/screen.** File: `src/pages/<PageName>Page.ts`
3. **Every step from the test case becomes one or more Playwright actions + assertion.**
4. **Pre-Requisites become `test.beforeEach` or fixture setup.**
5. **Test data comes from fixture files**, never hard-coded in specs.
6. **Every assertion maps to an Expected Result** from the test case. Add a comment with the step number.
7. **Use `test.describe` to group related test cases** (e.g., all TCs for one story).
8. **Locator strategy comes from project config.** Default: `data-testid`.

## UI Test Template

```typescript
// Test Case: TC_<STORY>_001 — <Summary>
// Story: <STORY-KEY>
// Component: UI

import { test, expect } from '../../src/fixtures/auth.fixture';
import { SomeFeaturePage } from '../../src/pages/SomeFeaturePage';

const testData = require('../../test-data/<feature>/valid.json');

test.describe('<Story Summary>', () => {
  let featurePage: SomeFeaturePage;

  test.beforeEach(async ({ authedPage }) => {
    // Pre-Requisites from test case
    featurePage = new SomeFeaturePage(authedPage);
    await featurePage.navigate();
  });

  test('TC_<STORY>_001 - <Test Summary>', async ({ authedPage }) => {
    // Step 1: <Action from test case>
    await featurePage.performAction(testData.input);
    // Expected Result Step 1: <Expected result>
    await expect(featurePage.resultElement).toBeVisible();

    // Step 2: <Action from test case>
    await featurePage.submitForm();
    // Expected Result Step 2: <Expected result>
    await expect(featurePage.successMessage).toHaveText('Saved successfully');

    // Final Expected Result: <Business outcome>
    await expect(featurePage.statusIndicator).toHaveText('Active');
  });

  test('TC_<STORY>_002 - Negative: <Test Summary>', async ({ authedPage }) => {
    // Negative test case...
    await featurePage.performAction(testData.invalidInput);
    await expect(featurePage.errorMessage).toBeVisible();
    await expect(featurePage.errorMessage).toContainText('Invalid');
  });
});
```

## Page Object Template

```typescript
import { type Page, type Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class SomeFeaturePage extends BasePage {
  protected readonly pageUrl = '/feature-path';

  // Locators — use project's locator strategy
  readonly heading: Locator;
  readonly inputField: Locator;
  readonly submitButton: Locator;
  readonly successMessage: Locator;
  readonly errorMessage: Locator;
  readonly statusIndicator: Locator;
  readonly resultElement: Locator;

  constructor(page: Page) {
    super(page);
    this.heading = this.getByTestId('feature-heading');
    this.inputField = this.getByTestId('input-field');
    this.submitButton = this.getByTestId('submit-button');
    this.successMessage = this.getByTestId('success-message');
    this.errorMessage = this.getByTestId('error-message');
    this.statusIndicator = this.getByTestId('status-indicator');
    this.resultElement = this.getByTestId('result-element');
  }

  async performAction(data: Record<string, string>): Promise<void> {
    for (const [field, value] of Object.entries(data)) {
      await this.getByTestId(`input-${field}`).fill(value);
    }
  }

  async submitForm(): Promise<void> {
    await this.submitButton.click();
    await this.page.waitForLoadState('networkidle');
  }
}
```

---

# 5. GENERATING API TESTS

When asked to generate API tests from a test case in quality_pack.json:

## Rules

1. **One spec file per service/endpoint group.** File: `tests/api/<service>/<endpoint>.spec.ts`
2. **One API Client per service.** File: `src/api/<ServiceName>Client.ts`
3. **Validate: status code, response body schema, specific field values, response time.**
4. **Test all HTTP methods** the endpoint supports (GET, POST, PUT, DELETE).
5. **Include negative tests**: invalid payloads, missing auth, wrong content-type, boundary values.
6. **Schema validation** for every response using a strict type check.
7. **Response time assertions** for performance-sensitive endpoints.

## API Test Template

```typescript
// Test Case: TC_<STORY>_005 — <Summary>
// Story: <STORY-KEY>
// Component: API

import { test, expect } from '@playwright/test';
import { SomeServiceClient } from '../../src/api/SomeServiceClient';

const validPayload = require('../../test-data/<service>/valid.json');
const invalidPayload = require('../../test-data/<service>/invalid.json');

let client: SomeServiceClient;

test.beforeAll(async ({ request }) => {
  const baseUrl = process.env.API_BASE_URL ?? 'http://localhost:8080';
  client = new SomeServiceClient(request, baseUrl);
});

test.describe('<Service> API - <Endpoint>', () => {

  test('TC_<STORY>_005 - Create resource with valid payload', async () => {
    // Step 1: Send POST request with valid data
    const response = await client.createResource(validPayload);

    // Expected Result Step 1: 201 Created
    await client.assertStatus(response, 201);

    // Step 2: Verify response body contains created resource
    expect(response.body).toHaveProperty('id');
    expect(response.body.name).toBe(validPayload.name);

    // Step 3: Verify response time is acceptable
    await client.assertResponseTime(response, 2000);

    // Final Expected Result: Resource exists and is retrievable
    const getResponse = await client.getResource(response.body.id);
    await client.assertStatus(getResponse, 200);
    expect(getResponse.body.name).toBe(validPayload.name);
  });

  test('TC_<STORY>_006 - Reject invalid payload', async () => {
    const response = await client.createResource(invalidPayload);
    await client.assertStatus(response, 400);
    expect(response.body).toHaveProperty('error');
  });

  test('TC_<STORY>_007 - Reject unauthorized request', async () => {
    const unauthClient = new SomeServiceClient(
      client['request'],
      client['baseUrl'],
      { skipAuth: true }
    );
    const response = await unauthClient.createResource(validPayload);
    await client.assertStatus(response, 401);
  });
});
```

## API Client Template

```typescript
import { type APIRequestContext } from '@playwright/test';
import { BaseApiClient, type ApiResponse } from './BaseApiClient';

export interface ResourcePayload {
  name: string;
  // Add fields per endpoint contract
}

export interface ResourceResponse {
  id: string;
  name: string;
  createdAt: string;
}

export class SomeServiceClient extends BaseApiClient {
  private skipAuth: boolean;

  constructor(request: APIRequestContext, baseUrl: string, options?: { skipAuth?: boolean }) {
    super(request, baseUrl);
    this.skipAuth = options?.skipAuth ?? false;
  }

  protected async getHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (!this.skipAuth) {
      headers['Authorization'] = `Bearer ${process.env.API_TOKEN ?? ''}`;
    }
    return headers;
  }

  async createResource(payload: ResourcePayload): Promise<ApiResponse<ResourceResponse>> {
    return this.post<ResourceResponse>('/api/v1/resources', payload);
  }

  async getResource(id: string): Promise<ApiResponse<ResourceResponse>> {
    return this.get<ResourceResponse>(`/api/v1/resources/${id}`);
  }

  async updateResource(id: string, payload: Partial<ResourcePayload>): Promise<ApiResponse<ResourceResponse>> {
    return this.put<ResourceResponse>(`/api/v1/resources/${id}`, payload);
  }

  async deleteResource(id: string): Promise<ApiResponse<void>> {
    return this.delete<void>(`/api/v1/resources/${id}`);
  }

  async listResources(params?: Record<string, string>): Promise<ApiResponse<ResourceResponse[]>> {
    return this.get<ResourceResponse[]>('/api/v1/resources', params);
  }
}
```

---

# 6. GENERATING DATA COMPARISON TESTS

When asked to generate data comparison tests from a test case in quality_pack.json:

## Rules

1. **One spec file per comparison scope.** File: `tests/data/<pipeline>/<comparison>.spec.ts`
2. **Use the DataComparisonEngine** with a config that defines key fields, field mappings, and tolerances.
3. **Source and target connectors** abstract where data comes from (DB, API, file).
4. **Every comparison must check**: record counts, field-level values, aggregation totals.
5. **Tolerance rules for financial data**: use `numericTolerance` from comparison config. Never use floating-point equality for money.
6. **Key fields must uniquely identify records.** If duplicates exist, fail fast with a clear message.
7. **Test data mapping files** define source→target field relationships. Store in `test-data/data-comparison/mapping/`.

## Data Comparison Test Template

```typescript
// Test Case: TC_<STORY>_010 — <Summary>
// Story: <STORY-KEY>
// Component: DataComparison

import { test, expect } from '@playwright/test';
import { DataComparisonEngine, type ComparisonConfig } from '../../src/data/DataComparisonEngine';

const sourceData = require('../../test-data/data-comparison/<pipeline>/source.json');
const targetData = require('../../test-data/data-comparison/<pipeline>/target.json');

const comparisonConfig: ComparisonConfig = {
  keyFields: ['accountId', 'securityId', 'effectiveDate'],
  fieldMappings: [
    { sourceField: 'accountId', targetField: 'account_id', compareAs: 'string' },
    { sourceField: 'securityId', targetField: 'security_id', compareAs: 'string' },
    { sourceField: 'marketValue', targetField: 'market_value', compareAs: 'number', tolerance: 0.01 },
    { sourceField: 'quantity', targetField: 'qty', compareAs: 'number', tolerance: 0 },
    { sourceField: 'currency', targetField: 'ccy', compareAs: 'string', transform: 'uppercase' },
    { sourceField: 'tradeDate', targetField: 'trade_date', compareAs: 'date' },
  ],
  aggregations: [
    { name: 'Total Market Value', sourceField: 'marketValue', targetField: 'market_value', tolerance: 0.05 },
    { name: 'Total Quantity', sourceField: 'quantity', targetField: 'qty', tolerance: 0 },
  ],
  nullEqualsEmpty: true,
  caseSensitive: false,
  numericTolerance: 0.001,
};

test.describe('Data Comparison: <Pipeline Name>', () => {

  test('TC_<STORY>_010 - Record count reconciliation', async () => {
    // Step 1: Count source records
    expect(sourceData.length).toBeGreaterThan(0);

    // Step 2: Count target records
    expect(targetData.length).toBeGreaterThan(0);

    // Expected Result: Counts match
    expect(sourceData.length).toBe(targetData.length);
  });

  test('TC_<STORY>_011 - Field-level data comparison', async () => {
    const engine = new DataComparisonEngine(comparisonConfig);
    const result = engine.compare(sourceData, targetData);

    // Step 1: Verify no missing records in target
    expect(result.missingInTarget, `${result.missingInTarget} records missing in target`).toBe(0);

    // Step 2: Verify no field mismatches
    if (result.fieldMismatches.length > 0) {
      const details = result.fieldMismatches.slice(0, 10).map(
        (m) => `Key=${m.recordKey} Field=${m.field} Source=${m.sourceValue} Target=${m.targetValue}`
      ).join('\n');
      expect(result.fieldMismatches.length, `Field mismatches found:\n${details}`).toBe(0);
    }

    // Final Expected Result: All records match
    expect(result.passed, result.summary).toBe(true);
  });

  test('TC_<STORY>_012 - Aggregation reconciliation', async () => {
    const engine = new DataComparisonEngine(comparisonConfig);
    const result = engine.compare(sourceData, targetData);

    // Verify each aggregation check
    for (const agg of result.aggregationChecks) {
      expect(agg.passed, `${agg.name}: source=${agg.sourceValue} target=${agg.targetValue} tolerance=${agg.tolerance}`).toBe(true);
    }
  });
});
```

## Database Connector (for live DB comparisons)

```typescript
export interface DbConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
}

export class DatabaseConnector {
  private config: DbConfig;

  constructor(config: DbConfig) {
    this.config = config;
  }

  async query(sql: string, params?: unknown[]): Promise<Record<string, unknown>[]> {
    // Implementation depends on the database driver (pg, mssql, mysql2, oracledb).
    // Each project configures its driver in package.json.
    // This method returns rows as plain objects.
    throw new Error('Implement with project-specific database driver');
  }

  async getSourceData(tableName: string, filter?: string): Promise<Record<string, unknown>[]> {
    const where = filter ? ` WHERE ${filter}` : '';
    return this.query(`SELECT * FROM ${tableName}${where}`);
  }

  async getRecordCount(tableName: string, filter?: string): Promise<number> {
    const where = filter ? ` WHERE ${filter}` : '';
    const result = await this.query(`SELECT COUNT(*) as cnt FROM ${tableName}${where}`);
    return Number(result[0].cnt);
  }

  async getAggregation(tableName: string, field: string, filter?: string): Promise<number> {
    const where = filter ? ` WHERE ${filter}` : '';
    const result = await this.query(`SELECT SUM(${field}) as total FROM ${tableName}${where}`);
    return Number(result[0].total ?? 0);
  }
}
```

---

# 7. PLAYWRIGHT CONFIGURATION

Generate a `playwright.config.ts` that supports all three test types:

```typescript
import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

dotenv.config();

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'results/junit-report.xml' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  projects: [
    // UI tests — run in browser
    {
      name: 'ui-chrome',
      testDir: './tests/ui',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'ui-firefox',
      testDir: './tests/ui',
      use: { ...devices['Desktop Firefox'] },
    },
    // API tests — no browser needed
    {
      name: 'api',
      testDir: './tests/api',
      use: { baseURL: process.env.API_BASE_URL ?? 'http://localhost:8080' },
    },
    // Data comparison tests — no browser needed
    {
      name: 'data-comparison',
      testDir: './tests/data',
      timeout: 120_000,
    },
  ],
});
```

---

# 8. CI/CD PIPELINE (GitHub Actions)

```yaml
name: Playwright Tests
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1-5'  # Weekdays 6am UTC

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project: [api, data-comparison, ui-chrome]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
        if: matrix.project == 'ui-chrome'
      - run: npx playwright test --project=${{ matrix.project }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: results-${{ matrix.project }}
          path: |
            results/
            playwright-report/
            screenshots/
```

---

# 9. ANTI-HALLUCINATION RULES

- **NEVER generate selectors you have not seen in the application.** If you do not know the actual testid/label, use a placeholder `[TODO: verify selector]` and flag it.
- **NEVER hard-code credentials, tokens, or URLs.** Always use `process.env` variables.
- **NEVER use `page.waitForTimeout()` or `sleep()`.** Use Playwright auto-waiting, `waitForResponse`, `waitForLoadState`, or `expect` with built-in polling.
- **NEVER use `page.locator('.css-class')` unless no semantic alternative exists.** Document why with a `// TODO: add data-testid` comment.
- **NEVER skip assertions.** Every test step must verify something. A test without assertions is not a test.
- **NEVER generate tests that depend on execution order.** Each test must be independently runnable.
- **NEVER use floating-point equality for financial amounts.** Always use tolerance-based comparison.
- **NEVER fabricate expected values.** Expected values come from the test case in quality_pack.json. If not specified, use a placeholder and flag it.
- **NEVER auto-commit generated code.** Output for human review only.

---

# 10. CROSS-TEAM USAGE

This skill is generic across all teams because:

1. **Project config drives everything** — locator strategy, base URLs, auth endpoints, DB connections
2. **Environment variables isolate environments** — same scripts run against QA, Staging, UAT
3. **Page Objects and API Clients are per-feature** — each team creates their own, extending the shared base
4. **Data Comparison Engine is config-driven** — field mappings and tolerances are external JSON files, not code
5. **CI/CD pipeline uses matrix strategy** — teams enable/disable test projects (ui, api, data) as needed

To adopt in a new team:
1. Set `automation.framework: "Playwright"` and `automation.language: "TypeScript"` in the project config
2. Run `npm init playwright@latest` in the automation repo
3. Copy `src/pages/BasePage.ts`, `src/api/BaseApiClient.ts`, `src/data/DataComparisonEngine.ts` from the shared framework
4. Generate tests using this skill: `@automation-agent Generate scripts for <STORY-KEY>`
5. Fill in the `[TODO]` placeholders with actual selectors/endpoints
6. Run: `npx playwright test`
