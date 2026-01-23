▼ ユーザーメッセージ受信（LINE webhook）
        ↓
（1）意図分類（intent detection, LLM または簡単キーワード併用）
        ↓
─────────────────────────────────
intent == FAQ？
→ YES：PGVector で RAG検索（embeddings → similarity 0.8以上）
→ 1件以上ヒット：　FAQとして回答
→ 0件： intent を再判定 → NO へ
─────────────────────────────────
intent != FAQ の場合 → 以下に振り分け

① intent: attendance（勤怠）
　→ プロンプトに基づきヒアリング

② intent: counseling（悩み相談）
　→ 傾聴 → 状況把握 → 面談提案

③ intent: escalation（重大案件）
　→ 即エスカレーション文言
　→ 管理者へ通知

④ intent: other（その他）
　→ スタイルに合わせて返答