# Partner Polaris MCP Server

AWS Partner Polaris Level 분석 MCP 서버. T&C 팀원들이 AI 어시스턴트를 통해 파트너 교육 깊이(Training Depth)를 조회, 계산, 벤치마크할 수 있습니다.

## Tools

| Tool | Description |
|------|-------------|
| `get_polaris_status` | 국가별 파트너 Polaris 레벨 현황 조회 |
| `calculate_polaris_level` | 입력값 기반 레벨 계산 (What-if 시뮬레이션) |
| `get_l3_gap_analysis` | L3 달성 갭 분석 + 우선순위 액션 가이드 |
| `get_polaris_benchmark` | 국가간 Polaris 벤치마크 비교 |
| `get_polaris_criteria` | 공식 Polaris 프레임워크 기준 조회 |

## 설치

### 1. Clone

```bash
git clone https://github.com/your-org/partner-polaris-mcp.git
cd partner-polaris-mcp
```

### 2. Install

```bash
pip install -e .
```

> Python 3.10+ 필요. 가상환경 사용 권장:
> ```bash
> python -m venv .venv
> .venv\Scripts\activate  # Windows
> source .venv/bin/activate  # macOS/Linux
> pip install -e .
> ```

### 3. 데이터 추가

`data/` 폴더에 자국 파트너 데이터 CSV를 추가합니다:

```bash
cp data/sample_korea.csv data/japan.csv  # 템플릿 복사 후 수정
```

커스텀 경로를 사용하려면 환경변수를 설정합니다:
```bash
export POLARIS_DATA_DIR=/path/to/your/data  # macOS/Linux
set POLARIS_DATA_DIR=C:\path\to\your\data   # Windows
```

## MCP 클라이언트 설정

### Kiro

`~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "partner-polaris": {
      "command": "python",
      "args": ["-m", "partner_polaris_mcp.server"],
      "cwd": "C:\\Users\\<your-alias>\\partner-polaris-mcp\\src",
      "env": {
        "POLARIS_DATA_DIR": "C:\\Users\\<your-alias>\\partner-polaris-mcp\\data"
      }
    }
  }
}
```

### Claude Desktop

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "partner-polaris": {
      "command": "python",
      "args": ["-m", "partner_polaris_mcp.server"],
      "cwd": "C:\\Users\\<your-alias>\\partner-polaris-mcp\\src",
      "env": {
        "POLARIS_DATA_DIR": "C:\\Users\\<your-alias>\\partner-polaris-mcp\\data"
      }
    }
  }
}
```

### Amazon Q Developer (VS Code)

`.vscode/mcp.json`:

```json
{
  "servers": {
    "partner-polaris": {
      "command": "python",
      "args": ["-m", "partner_polaris_mcp.server"],
      "cwd": "${workspaceFolder}/src",
      "env": {
        "POLARIS_DATA_DIR": "${workspaceFolder}/data"
      }
    }
  }
}
```

## 데이터 포맷

### CSV 컬럼

```csv
partner_name,tier,country,total_certs_ttm,foundational_certs,associate_certs,professional_certs,specialty_certs,ilt_sessions_total,ilt_sessions_int_plus,sb_subscription_engagements,sb_hands_on_completions,active_certs_3y
```

### 데이터 소스

1. QuickSight **"Global Partner Training & Certification"** 대시보드
2. **Self Service - Partner Certifications** 시트
3. Candidate Country 필터 → 자국 선택 → Export

## 예시 질문

```
"Korea 파트너 Polaris 현황 보여줘"
"Samsung SDS가 L3 달성하려면 뭐가 필요해?"
"Korea vs Japan 파트너 교육 비교"
"Premier 파트너가 250 certs, 200 Int+ 이면 레벨이?"
"Advanced 티어의 L3 요건이 뭐야?"
```

## Polaris 프레임워크 요약

### Dual-Condition Rule
L2/L3 레벨 부여를 위해 **두 조건 모두** 충족 필요:
- **조건1:** Total certifications >= 티어별 threshold
- **조건2:** Engagement Points >= 티어별 threshold

### Thresholds

| Tier | L2 Certs | L2 Pts | L3 Certs | L3 Pts |
|------|----------|--------|----------|--------|
| Select | 5 | 5 | 20 | 20 |
| Advanced | 10 | 10 | 40 | 40 |
| Premier | 100 | 100 | 400 | 400 |

### Point 계산
- **L2 Points:** ILT 1석 = 1pt, Cert 1개 = 1pt, SB Sub 5개 = 1pt
- **L3 Points:** Int+ ILT 1석 = 1pt, Int+ Cert 1개 = 1pt, Hands-on SB 5개 = 1pt
- **Int+** = Associate + Professional + Specialty (Foundational 제외)

## 프로젝트 구조

```
partner-polaris-mcp/
├── src/partner_polaris_mcp/
│   ├── server.py          # MCP Tool 정의 (FastMCP)
│   ├── polaris_engine.py  # 레벨 계산 로직
│   ├── gap_analyzer.py    # L3 갭 분석 & 추천
│   ├── benchmark.py       # 국가간 벤치마킹
│   ├── data_loader.py     # CSV 로딩 & 캐싱
│   └── models.py          # 데이터 모델
├── data/
│   ├── polaris_criteria.json  # 레벨 threshold 설정
│   ├── sample_korea.csv       # 샘플 데이터
│   └── country_mapping.json   # 리전/국가 매핑
├── pyproject.toml
└── README.md
```

## Contributing

1. `data/`에 자국 CSV 추가
2. `get_polaris_status(country="YourCountry")`로 테스트
3. PR 또는 Slack #tc-polaris-mcp로 피드백

## License

Internal AWS use only.
