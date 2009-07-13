#set style data histograms
#set style histogram rowstacked
#set style fill solid border -1
set log xy

set terminal png butt size 2000, 1200 x000000 xffffff x0000ff xff0000 
set output "hist.png"

#plot 'hist.dat' using 1 w p t 'Common', '' using 2  w p t 'Sysop'
plot 'hist.dat' u ($0+1):1 w histeps t 'Common', '' u ($0+1):2  w histeps t 'Sysop', '' u ($0+1):3  w histeps t 'Bureaucrat', '' u ($0+1):4  w histeps t 'Steward', '' u ($0+1):5  w histeps t 'Founder', '' u ($0+1):6  w histeps t 'Bots'
#pause -1
