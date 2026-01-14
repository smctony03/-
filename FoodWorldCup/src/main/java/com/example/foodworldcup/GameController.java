package com.example.foodworldcup;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@Controller
public class GameController {
    @Autowired
    private FoodRepository foodRepository;

    @GetMapping("/")
    public String index() {
        return "index";
    }

    @PostMapping("/start-custom")
    public String startCustomGame(@RequestParam("myFoods") String myFoods,
                                  @RequestParam(name = "round", defaultValue = "8") int round,
                                  @RequestParam(name = "mode", defaultValue = "solo") String mode,
                                  @RequestParam(name = "totalPeople", defaultValue = "1") int totalPeople,
                                  Model model) {
        List<Food> gameFoods = createGameFoods(myFoods, round);
        model.addAttribute("foods", gameFoods);
        model.addAttribute("mode", mode);
        model.addAttribute("myFoodsRaw", myFoods);
        model.addAttribute("roundRaw", round);
        model.addAttribute("currentPerson", 1);
        model.addAttribute("totalPeople", totalPeople);
        model.addAttribute("accumulatedHistory", "");
        return "game";
    }

    @PostMapping("/next-person")
    public String nextPerson(@RequestParam("myFoods") String myFoods,
                             @RequestParam("round") int round,
                             @RequestParam("currentPerson") int currentPerson,
                             @RequestParam("totalPeople") int totalPeople,
                             @RequestParam("historyData") String historyData,
                             @RequestParam("accumulatedHistory") String accumulatedHistory,
                             Model model) {
        String newHistory = accumulatedHistory.isEmpty() ? historyData : accumulatedHistory + "|" + historyData;
        if (currentPerson >= totalPeople) {
            String[] aiResult = safeRunPython(newHistory);
            String finalFoodName = aiResult[0];
            String finalReason = aiResult[1];
            Food winnerFood = getOrCreateFood(finalFoodName);
            model.addAttribute("allPicks", newHistory.replace("|", ",").split(","));
            model.addAttribute("finalFood", finalFoodName);
            model.addAttribute("finalReason", finalReason);
            model.addAttribute("finalImgUrl", winnerFood.getImgUrl());
            return "multi_result";
        }
        List<Food> gameFoods = createGameFoods(myFoods, round);
        model.addAttribute("foods", gameFoods);
        model.addAttribute("mode", "multi");
        model.addAttribute("myFoodsRaw", myFoods);
        model.addAttribute("roundRaw", round);
        model.addAttribute("currentPerson", currentPerson + 1);
        model.addAttribute("totalPeople", totalPeople);
        model.addAttribute("accumulatedHistory", newHistory);
        return "game";
    }

    @GetMapping("/result")
    public String showResult(@RequestParam("winner1") String w1Name,
                             @RequestParam("winner2") String w2Name,
                             @RequestParam(value = "history", required = false, defaultValue = "") String history,
                             Model model) {
        Food f1 = getOrCreateFood(w1Name);
        Food f2 = getOrCreateFood(w2Name);
        String inputData = history + "," + w1Name + "," + w2Name;
        String[] aiResult = safeRunPython(inputData);
        Food f3 = getOrCreateFood(aiResult[0]);
        model.addAttribute("card1", f1);
        model.addAttribute("card2", f2);
        model.addAttribute("card3", f3);
        return "result";
    }

    // ================= 수정된 Python 실행 메서드 =================
    private String[] safeRunPython(String foodList) {
        StringBuilder output = new StringBuilder();
        try {
            // 1. 파이썬 실행 경로와 스크립트 경로
            String pythonPath = "C:\\anaconda\\python.exe";
            String scriptPath = "C:\\한국공학대학교 2025년 2학기 자바실습\\FoodWorldCup\\src\\recommend.py";

            ProcessBuilder pb = new ProcessBuilder(pythonPath, scriptPath, foodList);
            pb.redirectErrorStream(true); // 에러 출력을 표준 출력에 합침
            Process p = pb.start();

            // 2. UTF-8 인코딩으로 파이썬 출력 읽기
            BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream(), "UTF-8"));
            String line;
            while ((line = br.readLine()) != null) {
                // 자바 IDE 콘솔에서 파이썬의 진행 상황과 에러를 실시간 확인
                System.out.println("[Python Debug]: " + line);
                output.append(line).append("\n");
            }
            p.waitFor();

            String fullResult = output.toString().trim();
            if (fullResult.isEmpty()) return new String[]{"분석불가", "파이썬으로부터 응답을 받지 못했습니다."};

            // 3. 파이썬이 출력한 내용 중 가장 마지막 줄을 결과로 취급
            String[] lines = fullResult.split("\n");
            String lastLine = lines[lines.length - 1];

            if (lastLine.contains("|")) {
                return lastLine.split("\\|");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        // 예외 발생 시 반환할 기본값
        return new String[]{"비빔밥", "AI 추천 서비스에 일시적인 문제가 있어 기본 메뉴를 추천합니다."};
    }

    private Food getOrCreateFood(String name) {
        List<Food> all = foodRepository.findAll();
        for (Food f : all) if (f.getName().equals(name)) return f;

        Food temp = new Food();
        temp.setName(name);
        temp.setImgUrl("");
        return temp;
    }

    private List<Food> createGameFoods(String myFoods, int round) {
        List<Food> gameFoods = new ArrayList<>();
        if (myFoods != null && !myFoods.isEmpty()) {
            for (String name : myFoods.split(",")) {
                if (!name.trim().isEmpty()) gameFoods.add(getOrCreateFood(name.trim()));
            }
        }
        int needed = round - gameFoods.size();
        if (needed > 0) {
            List<Food> dbFoods = foodRepository.findAll();
            Collections.shuffle(dbFoods);
            for (Food f : dbFoods) {
                if (gameFoods.size() >= round) break;
                if (gameFoods.stream().noneMatch(ef -> ef.getName().equals(f.getName()))) gameFoods.add(f);
            }
        }
        Collections.shuffle(gameFoods);
        return gameFoods;
    }
}