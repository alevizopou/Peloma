import numpy as np
import matplotlib.pyplot as plt

n_groups = 3

means_1 = (1, 1, 2)
means_2 = (1, 1, 1)
means_3 = (4, 3, 5)
means_4 = (16, 10, 19)
means_5 = (28, 35, 23)

fig, ax = plt.subplots()

index = np.arange(n_groups)  # the x locations for the groups
bar_width = 0.15  # the width of the bars: can also be len(x) sequence

opacity = 0.4
error_config = {'ecolor': '0.3'}

rects1 = plt.bar(index, means_1, bar_width,
                 alpha=opacity,
                 color='b',
                 error_kw=error_config,
                 label='Execrable')

rects2 = plt.bar(index + bar_width, means_2, bar_width,
                 alpha=opacity,
                 color='red',
                 error_kw=error_config,
                 label='Below Average')

rects3 = plt.bar(index + bar_width + bar_width, means_3, bar_width,
                 alpha=opacity,
                 color='orange',
                 error_kw=error_config,
                 label='Average')

rects4 = plt.bar(index + bar_width + bar_width + bar_width, means_4, bar_width,
                 alpha=opacity,
                 color='yellow',
                 error_kw=error_config,
                 label='Above Average')

rects5 = plt.bar(index + bar_width + bar_width + bar_width + bar_width, means_5, bar_width,
                 alpha=opacity,
                 color='white',
                 # yerr=std_child3,
                 error_kw=error_config,
                 label='Exceptional')

plt.xlabel('')
plt.ylabel('# of votes')
plt.title('Αξιολόγηση των προτάσεων του συστήματος')
plt.xticks(index + bar_width + bar_width + (bar_width/2), ('Preference', 'Diversity', 'Ordering'))
plt.yticks(np.arange(0, 50, 5))
plt.legend(prop={'size': 12}, loc='upper left')


def autolabel(rects):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%d' % int(height),
                ha='center', va='bottom')

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)
autolabel(rects4)
autolabel(rects5)

plt.tight_layout()
# plt.show()
plt.savefig('foo.png', bbox_inches='tight')
