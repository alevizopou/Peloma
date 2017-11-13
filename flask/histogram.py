"""
Bar chart demo with pairs of bars grouped for easy comparison.
"""
import numpy as np
import matplotlib.pyplot as plt

n_groups = 3

means_men = (1, 1, 2)
# std_men = (1, 3, 4)

means_women = (1, 1, 1)
# std_women = (3, 5, 2)

means_child = (4, 3, 5)
# std_child = (4, 2, 4)

means_child2 = (16, 10, 19)
# std_child2 = (4, 2, 4)

means_child3 = (28, 35, 23)
# std_child3 = (4, 2, 4)

fig, ax = plt.subplots()

index = np.arange(n_groups)  # the x locations for the groups
bar_width = 0.15  # the width of the bars: can also be len(x) sequence

opacity = 0.4
error_config = {'ecolor': '0.3'}

rects1 = plt.bar(index, means_men, bar_width,
                 alpha=opacity,
                 color='b',
                 error_kw=error_config,
                 label='Execrable')

rects2 = plt.bar(index + bar_width, means_women, bar_width,
                 alpha=opacity,
                 color='red',
                 error_kw=error_config,
                 label='Below Average')

rects3 = plt.bar(index + bar_width + bar_width, means_child, bar_width,
                 alpha=opacity,
                 color='orange',
                 error_kw=error_config,
                 label='Average')

rects4 = plt.bar(index + bar_width + bar_width + bar_width, means_child2, bar_width,
                 alpha=opacity,
                 color='yellow',
                 error_kw=error_config,
                 label='Above Average')

rects5 = plt.bar(index + bar_width + bar_width + bar_width + bar_width, means_child3, bar_width,
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
# plt.legend((rects1[0], rects2[0]), ('Men', 'Women'))
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