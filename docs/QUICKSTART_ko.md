# Document Studio 빠른 시작

**AI가 바뀌어도, 우리 회사의 문서 기준은 유지합니다.**

기존 문서를 분석해 **승인된 문체·디자인·레이아웃 규칙**을 재사용하는 맞춤형 ChatGPT 문서 제작 플러그인 툴킷입니다.

[English README](../README.md) · [관리자 배포 가이드](WORKSPACE_ADMIN_GUIDE.md) · [5단계 시연 흐름](DEMO_FLOW.md) · [日本語](QUICKSTART_ja.md)

## 어떤 문제를 해결하나요?

AI 모델과 버전, 사용하는 직원이 달라지더라도 기업의 보고서·제안서에는 공통의 문장 표현, 색상, 정보 배치 및 검수 기준이 필요합니다. Document Studio는 허가받은 PDF/PPTX를 분석해 작성·시각적 특성의 **근거**를 수집하고, 담당자가 결과를 검토·승인한 **Company Pack**을 문서 제작 워크플로우에 적용하도록 돕습니다.

핵심 흐름은 **자료 제공 → 스타일 분석 → 관리자 검토·승인 → 맞춤형 ZIP 내보내기 → 새로운 문서 제작**입니다. 일부 단계는 아직 수동이며, 한 번의 업로드로 끝나는 자동 서비스는 아닙니다. **AI 환경 변화에 독립적으로 관리할 수 있는 업무 규칙을 지향하지만, 모델 간 완전히 동일한 결과를 보장하지는 않습니다.**

## 지금 실행할 수 있는 가상 기업 데모

```bash
git clone https://github.com/wlehd00000-cell/document-studio.git
cd document-studio
python scripts/install_local.py --verify-only
python scripts/export_company_plugin.py \
  --company-pack company-packs/demo-retail \
  --language-skills ko,ja \
  --output ./dist/demo-retail-documents.zip
```

이 명령은 **독립 제작한 가상 기업 자료**로 맞춤형 플러그인 ZIP을 생성합니다. ChatGPT에 설치하거나 워크스페이스에 배포하는 작업은 별도입니다. [자세한 절차](WORKSPACE_ADMIN_GUIDE.md)를 확인하세요.

## 현재 버전의 중요한 제약

- **`v0.1.0-alpha.6` 실험판**입니다. 사내 비공개·접근 제한 원본으로 만든 Company Pack은 현재 공개용 내보내기 도구가 **차단**합니다. 사내 전용 비공개 배포 기능은 후속 개발 범위입니다.
- 사용자는 출처와 폰트·이미지 사용권을 확인하고 승인 규칙을 직접 검토해야 합니다.
- HTML/PPTX 최종 제작, 시각 검수, 브라우저 검증은 별도로 수행해야 합니다.
- 비즈니스 워크스페이스의 플러그인 설치·공개는 관리자의 권한과 플랫폼 지원 여부에 따라 달라집니다.

처음에는 위의 가상 기업 팩으로 검증하는 것을 권장합니다. 소스와 MIT 라이선스는 [GitHub 메인 페이지](../README.md)에서 확인할 수 있습니다.
