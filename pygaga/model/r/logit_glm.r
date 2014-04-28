data <- read.table("{{data_file}}", header=TRUE)
xnam <- names(data)
xnam <- xnam[xnam != "result"]
fmla <- as.formula(paste("~", paste(xnam, collapse = "+")))
pr <- prcomp(fmla, data, center = TRUE, scale = TRUE)
sd <- pr$sdev
rotation <- as.data.frame(pr$rotation)
pca_data <- as.data.frame(pr$x)
center <- pr$center
scale <- pr$scale
pr <- NULL
g <- gc()
s <- sum(sd)
xnam <- c()
sum_s <- 0
i = 0
for (name in names(rotation)) {
    i <- i+1
    sum_s <- sum_s + sd[i]
    if (sum_s > 0.90 * s) {
        break
    }
    xnam <- c(xnam, name)
}
rotation <- rotation[, (names(rotation) %in% xnam)]
pca_data <- pca_data[, (names(pca_data) %in% xnam)]
fmla <- as.formula(paste("result ~ ", paste(xnam, collapse = "+")))
pca_data$result <- round(data$result*10)/10
data <- NULL
g <- gc()
glm.sol <- glm(fmla, pca_data, family={{family}}(), weights=rep(10, length(pca_data$result)))
glm.sol.coef <- coef(glm.sol)
glm.sol.coef_for_z <- glm.sol.coef[2:length(glm.sol.coef)]
glm.sol.intercept <- glm.sol.coef[1] - sum(t(as.matrix(rotation) * center / scale) * glm.sol.coef_for_z)
glm.sol.coef_for_x <- glm.sol.coef_for_z %*% t(rotation) / scale
glm.sol.model <- c(glm.sol.intercept, glm.sol.coef_for_x[,])
if (glm.sol$converged) {
    write.table(glm.sol.model, file = "{{output_file}}")
} else {
    write.table(glm.sol.model, file = paste("{{output_file}}", ".error", sep=""))
}
