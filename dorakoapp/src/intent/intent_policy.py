# Intentごとの処理ルールを定義

class IntentRule:
    """
    Intentごとの挙動設定
    use_rag: RAG検索を使うか
    source_type: 参照するデータ種類
    """
    def __init__(self, use_rag: bool, source_type: str | None):
        self.use_rag = use_rag
        self.source_type = source_type

class IntentPolicy:
    """
    Intent分類結果からIntentRuleを返す
    """
    def get_rule(self, intent):
        if intent.value == "casual":
            return IntentRule(False, None)
        if intent.value == "hr_general":
            return IntentRule(True, "manual")
        if intent.value == "hr_personal":
            return IntentRule(True, "line_history")
        if intent.value == "retirement":
            return IntentRule(False, None)

        return IntentRule(False, None)
