appscope-analyzer
=======

`appscope-analyzer` is a command-line tool that parses the [AppScope][] logs
 and produces per process (PID) or per application (UID) power consumption
 information

### About AppScope

[AppScope][] is an application energy metering framework for Android smartphones
using kernel activity monitoring.

Understanding the energy consumption of a smartphone application is a key area of
interest for end users, as well as application and system software developers. Other
similar work has only been able to provide limited information concerning the energy
consumption of individual applications because of limited access to underlying hardware
and system software. The energy consumption of a smartphone application is, therefore,
often estimated with low accuracy and granularity. [AppScope][] is an Android-based energy
metering system. This system monitors application’s hardware usage at the kernel level
and accurately estimates energy consumption. [AppScope][] is implemented as a kernel module
and uses an event-driven monitoring method that generates low overhead and provides high
accuracy. Our preliminary evaluation results indicate that [AppScope][] accurately estimates
the energy consumption of Android applications expending approximately 35mW and 2.1% in
power consumption and CPU utilization overhead, respectively. 

[AppScope]: http://css3.yonsei.ac.kr:5612/appscope



Installing appscope-analyzer
------------

`appscope-analyzer` requires [Python][] 2.5 or newer, and some form of UNIX-like shell (bash
works well).  It works on Linux, OS X, and Windows (with [Cygwin][]).

[Python]: http://python.org/
[Cygwin]: http://www.cygwin.com/

Installing and setting up `appscope-analyzer` will take about one minute.

First, [download][] the tool or clone the [Mercurial repository][]. Next, open your `~/.bashrc` file and
put an alias there:

[download]: https://bitbucket.org/tpetsas/appscope-analyzer/get/d2d143e2711a.zip

  alias asa='python ~/path/to/appscope-analyzer.py'

Make sure you run `source ~/.bashrc` or restart your terminal window to make
the alias take effect.


Using appscope-analyzer
-------

`appscope-analyzer` is quick and easy to use.

### List Monitored Apps

To show a list of the monitored apps use `asa -s HT181P8A0128/ -l`


    PID     UID     APP PACKAGE
    ...     ...     ...
    344     10066   com.webroot.security                     
    659     10058   com.antivirus                            
    660     10058   com.antivirus                            
    665     10058   com.antivirus                            
    1157    10075   jackpal.androidterm
    ...     ...     ...

(`-q` option is available to hide PID column)

### Show Energy Of a Particular App/Process

To show the AppScope energy samples of a spesific app you can use:
`asa -s HT181P8A0128/ -u 10066` or
`asa -s HT181P8A0128/ -a com.webroot.security`


    TIME  CPU       DISPLAY  GPS       WIFI    3G       TOTAL
    2      34.2537  0.0000   0.0000    0.0000  0.0000    34.2537
    3     548.0595  0.0000   0.0000    0.0000  0.0000   548.0595
    4     542.8593  0.0000   0.0000    0.0000  0.0000   542.8593
    5     542.3506  0.0000   0.0000    0.0000  0.0000   542.3506
    6     542.6931  0.0000   0.0000    0.0000  0.0000   542.6931
    7     559.4774  0.0000   0.0000    0.0000  0.0000   559.4774
    8     553.9380  0.0000   0.0000    0.0000  0.0000   553.9380
    9     548.0595  0.0000   0.0000    0.0000  0.0000   548.0595
    10    548.1748  0.0000   0.0000    0.0000  0.0000   548.1748
    ...   ...       ...      ...       ...     ...      ...

To show the energy samlpes of a spesific process just use:
`asa -s HT181P8A0128/ -p 344`

(`-q` option will produce an output with only the 'TIME' and 'TOTAL' columns
`-v` option will produce a more detailed output containing usage information
such as CPU frequency ticks, packets send and received through WIFI, display
usage information etc.)


Tips and Tricks
---------------

You can search for a specific pattern in the output by using the
`-g` option. e.g.

`asa -s HT181P8A0128/ -l -g 'google'`


    PID     UID     APP PACKAGE
    ...     ...     ...
    307     1000    com.google.android.backup                
    308     1000    com.google.android.backup                
    2765    10034   com.google.android.inputmethod.latin     
    5140    10026   com.google.android.syncadapters.contacts 
    5265    1000    com.google.android.backup
    ...     ...     ...


Problems, Contributions, Etc
----------------------------

If you need anything beyond the basics `appscope-analyzer`
currenly provides you can find my contact details at [my website][].

[my website]: http://thanasispetsas.com

If you want to contribute code to `appscope-analyzer`, that's great!  Fork the
[Mercurial repository][] on BitBucket or the [git mirror][] on GitHub and send me
a pull request.

[Mercurial repository]: https://tpetsas@bitbucket.org/tpetsas/appscope-analyzer.git 
[git mirror]: https://github.com/tpetsas/appscope-analyzer.git
