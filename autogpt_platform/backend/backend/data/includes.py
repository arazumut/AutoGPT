import prisma

# Ajan Düğümü Dahil Etme
AJAN_DUGUM_DAHIL_ET: prisma.types.AgentNodeInclude = {
    "Girdi": True,
    "Çıktı": True,
    "Webhook": True,
    "AjanBlok": True,
}

# Ajan Grafiği Dahil Etme
AJAN_GRAFIGI_DAHIL_ET: prisma.types.AgentGraphInclude = {
    "AjanDüğümleri": {"include": AJAN_DUGUM_DAHIL_ET}  # type: ignore
}

# Yürütme Sonucu Dahil Etme
YURUTME_SONUCU_DAHIL_ET: prisma.types.AgentNodeExecutionInclude = {
    "Girdi": True,
    "Çıktı": True,
    "AjanDüğümü": True,
    "AjanGrafiğiYürütme": True,
}

# Grafik Yürütme Dahil Etme
GRAFIK_YURUTME_DAHIL_ET: prisma.types.AgentGraphExecutionInclude = {
    "AjanDüğümüYürütmeleri": {
        "include": {
            "Girdi": True,
            "Çıktı": True,
            "AjanDüğümü": True,
            "AjanGrafiğiYürütme": True,
        }
    }
}

# Entegrasyon Webhook Dahil Etme
ENTEGRASYON_WEBHOOK_DAHIL_ET: prisma.types.IntegrationWebhookInclude = {
    "AjanDüğümleri": {"include": AJAN_DUGUM_DAHIL_ET}  # type: ignore
}
