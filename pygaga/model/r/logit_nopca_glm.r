turnout <- read.table("{{data_file}}", header=TRUE)
xnam <- names(turnout)
xnam <- xnam[xnam != "result"]
fmla <- as.formula(paste("result ~", paste(xnam, collapse = "+")))
x=glm(fmla, data=turnout, family={{family}}())
write.table(coef(x),file="{{output_file}}")
