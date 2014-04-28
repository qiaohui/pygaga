data <- read.table("{{row_file}}", header=TRUE)
xnames <- names(data)
xnames <- xnames[xnames != "result"]
s <- floor(seq(0, length(xnames), length(xnames)/{{split_count}}))
filenames <- c( "{{filenames|join('","')}}" )
for (i in 1:{{split_count}}) {
  g<-gc()
  select_xnames <- xnames[(s[i] +1) : s[i + 1]]
  select_data <- data[, names(data) %in% select_xnames]
  select_data$result <- data$result
  write.table(select_data, filenames[i])
}

