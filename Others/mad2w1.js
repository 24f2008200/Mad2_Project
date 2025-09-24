/*
 * calculateSimpleInterest calculates and returns the simple interest
 * (floor value) for a fixed deposit. Formula used is,

 * calculateSimpleInterest calculates and returns the simple interest
 * for a fixed deposit. Formula used is,
 * Simple Interest: P X R X T / 100
 *   where:
 *   P = Principal
 *   I = Daily interest rate
 *   N = Number of days
 *
 *  In case of any input error (wrong date format, alphabets in daily interest etc.), return -1
 *
 * @param {number} principal  - Principal amount
 * @param {number} dailyInterest  - daily interest rate
 * @param {string} startingDate  - Starting date of the fixed deposit in "YYYY-MM-DD" format, example "2015-03-25"
 * @param {string} endingDate  - Ending date of the fixed deposit in "YYYY-MM-DD" format, example "2015-03-25"
 * @return {number} interest
*/

/*
 * calculateCompoundInterest calculates and returns the compound interest
 * (floor value) for a fixed deposit. Formula used is,
 *   Compound Interest=P[(1+I/100)^N - 1]
 *   where:
 *   P = Principal
 *   I = Daily interest rate
 *   N = Number of days
 *
 *  In case of any input error (wrong date format, alphabets in daily interest etc.), return -1
 *
 * @param {number} principal  - Principal amount
 * @param {number} dailyInterest  - daily interest rate
 * @param {string} startingDate  - Starting date of the fixed deposit in "YYYY-MM-DD" format, example "2015-03-25"
 * @param {string} endingDate  - Ending date of the fixed deposit in "YYYY-MM-DD" format, example "2015-03-25"
 * @return {number} interest
*/

/*
 * extraAmountPercentage calculates and returns the extra amount percentage borrower will have to pay in case of
 * compound interest (floor value) in comparison to the simple interest for a fixed deposit.

 *  In case of any input error (wrong date format, alphabets in daily interest etc.), return -1
 *
 * @param {number} principal  - Principal amount
 * @param {number} dailyInterest  - Daily interest rate.
 * @param {string} startingDate  - Starting date of the fixed deposit in "YYYY-MM-DD" format, example "2015-03-25"
 * @param {string} endingDate  - Ending date of the fixed deposit in "YYYY-MM-DD" format, example "2015-03-25"
 * @return {number} percentage
*/
function daysBetween(startingDate, endDate) {
    try {
        const start = new Date(startingDate);
        const end = new Date(endDate);
        if (isNaN(start.getTime()) || isNaN(end.getTime())) {
            return -1;
        }
        const diffMs = end - start;
        if (diffMs < 0) return -1;
        const diffDays = diffMs / (1000 * 60 * 60 * 24);
        return Math.floor(diffDays);
    } catch (error) {
        return -1;
    }
}

function calculateSimpleInterest(
    principal,
    dailyInterest,
    startingDate,
    endingDate
) {
    let number_of_days = daysBetween(startingDate, endingDate)
    if (
        typeof principal !== "number" || principal < 0 ||
        typeof dailyInterest !== "number" || dailyInterest < 0 || number_of_days < 0
    ) {
        return -1;
    }
    let interest = principal * dailyInterest * (number_of_days) / 100

    return Math.floor(interest);

}

function calculateCompoundInterest(
    principal,
    dailyInterest,
    startingDate,
    endingDate
) {
    let number_of_days = daysBetween(startingDate, endingDate)
    if (
        typeof principal !== "number" || principal < 0 ||
        typeof dailyInterest !== "number" || dailyInterest < 0 || number_of_days < 0
    ) {
        return -1;
    }
    let interest = principal * ((1 + dailyInterest/100) ** (number_of_days) - 1)

    return Math.floor(interest);

}

function extraAmountPercentage(
    principal,
    dailyInterest,
    startingDate,
    endingDate
) {

    let compound_interest = calculateCompoundInterest(
        principal,
        dailyInterest,
        startingDate,
        endingDate
    )
    let simple_interest = calculateSimpleInterest(
        principal,
        dailyInterest,
        startingDate,
        endingDate
    )
    if (simple_interest <= 0 || compound_interest < 0) {
        return -1
    } else {
        percentage = (compound_interest / simple_interest - 1) * 100

        return Math.floor(percentage);
    }

}

let principal = 100;
let dailyInterest = 12 / 360;
let startingDate = "2014-03-05"
let endingDate = "2015-03-25"

console.log(calculateSimpleInterest(
    principal,
    dailyInterest,
    startingDate,
    endingDate
));
console.log(calculateCompoundInterest(
    principal,
    dailyInterest,
    startingDate,
    endingDate
));
console.log(extraAmountPercentage(
    principal,
    dailyInterest,
    startingDate,
    endingDate
));
console.log(5 + "5");  // "55" (number + string → string)
console.log(5 - "2");  // 3   (string converted to number)
