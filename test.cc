// Example C++ file for testing src2html
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

/**
 * A simple class demonstrating various C++ features
 */
class Calculator {
private:
    std::vector<double> history;
    
public:
    Calculator() = default;
    
    double add(double a, double b) {
        double result = a + b;
        history.push_back(result);
        return result;
    }
    
    double multiply(double a, double b) {
        double result = a * b;
        history.push_back(result);
        return result;
    }
    
    // Template function for generic operations
    template<typename Func>
    double apply(double a, double b, Func operation) {
        double result = operation(a, b);
        history.push_back(result);
        return result;
    }
    
    void printHistory() const {
        std::cout << "Calculation history:" << std::endl;
        for (size_t i = 0; i < history.size(); ++i) {
            std::cout << "  [" << i << "] " << history[i] << std::endl;
        }
    }
};

int main() {
    Calculator calc;
    
    // Basic operations
    std::cout << "5 + 3 = " << calc.add(5, 3) << std::endl;
    std::cout << "4 * 7 = " << calc.multiply(4, 7) << std::endl;
    
    // Lambda with template
    auto subtract = [](double a, double b) { return a - b; };
    std::cout << "10 - 4 = " << calc.apply(10, 4, subtract) << std::endl;
    
    calc.printHistory();
    
    return 0;
}
