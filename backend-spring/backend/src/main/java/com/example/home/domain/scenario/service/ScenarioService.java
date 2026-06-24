package com.example.home.domain.scenario.service;

import com.example.home.domain.scenario.dto.CreateScenarioRequest;
import com.example.home.domain.scenario.dto.ScenarioDocument;
import com.example.home.domain.scenario.dto.ScenarioRoundExplanation;

public interface ScenarioService {

    ScenarioDocument create(CreateScenarioRequest request);

    ScenarioDocument get(String scenarioId);

    ScenarioRoundExplanation explainRound(String scenarioId, int relativeMonth);
}
