from numpy import genfromtxt
from numpy import ones
from numpy import zeros
from numpy import sort
from numpy import argsort
from numpy import where
#from scipy.linalg import block_diag
from numpy import multiply
from numpy import dot
from numpy import transpose
from numpy import copy
from numpy import random
import time

tstart=time.time()
#Import list of student ids
ID = genfromtxt('ids.csv', delimiter=',')
### Modify this to the prefs file you use to run the algorithm.
Prefs = genfromtxt('variant_1.csv', delimiter=',')
#Sort list of ids, probably should confirm that there are no duplicates
ID=sort(ID)
#NumIDs is the number of people to assign to groups. Add additional blanks so it is an multiple of 4
NumIDs=(int((len(ID)-1)/4)+1)*4
#Create Preferene Matrix, with an extra row for IDs
PrefMat=zeros((NumIDs+1,NumIDs))
#Insert list of ids in last row of Preference Matrix
PrefMat[-1,0:len(ID)]=ID
#Loop through preferences and put numbers into Preference Matrix
for i in range(0, len(Prefs)):
    PrefMat[where(Prefs[i,0]==ID),where(Prefs[i,1]==ID)]=Prefs[i,2]
#Create a block diagonal matrix to assign groups
t=ones((4,4))
numteams=int(NumIDs/4)
#Rept=[t]*numteams
#teams=block_diag(*Rept)

teams=zeros((NumIDs,NumIDs))
for i in range(0,numteams):
    teams[i*4:(i+1)*4,i*4:(i+1)*4]=t

NumNoPrefs=sum(dot(PrefMat[0:NumIDs,:]>0,ones((NumIDs,1)))==0)
BestMax = -30*NumIDs

def count_no_positive_teammates(groups, prefs):
    count = 0
    students_with_prefs = [item[0] for item in prefs]
    # Convert matrix format of prefs to dict format
    if not isinstance(prefs, dict):
        prefs_matrix = prefs
        ids_list = list(prefs_matrix[-1, :])
        prefs = {}
        for i in range(len(ids_list)):
            for j in range(len(ids_list)):
                if i != j:
                    prefs[(ids_list[i], ids_list[j])] = prefs_matrix[i, j]

    # Iterate through each group
    for group in groups:
        # For each member in the group, check if they have a positively scored teammate
        for student in group:
            has_positive_teammate = False
            for teammate in group:
                if teammate != student and prefs.get((student, teammate), 0) > 0:
                    has_positive_teammate = True
                    break
            if not has_positive_teammate and student in students_with_prefs:
                count += 1

    return count

def count_no_negative_teammates(groups, prefs):
    """
    Count the number of students who didn't get a teammate with a positive score.

    Parameters:
    - groups: A list of lists (or array) where each inner list/array contains IDs of students grouped together.
    - prefs: Preference data in a dictionary format {(student_id, teammate_id): score} or a matrix.

    Returns:
    - Count of students with negatively scored teammate.
    """

    count = 0

    # Convert matrix format of prefs to dict format
    if not isinstance(prefs, dict):
        prefs_matrix = prefs
        ids_list = list(prefs_matrix[-1, :])
        prefs = {}
        for i in range(len(ids_list)):
            for j in range(len(ids_list)):
                if i != j:
                    prefs[(ids_list[i], ids_list[j])] = prefs_matrix[i, j]

    # Iterate through each group
    for group in groups:
        # For each member in the group, check if they have a positively scored teammate
        for member in group:
            has_negative_teammate = False
            for teammate in group:
                if teammate != member and prefs.get((member, teammate), 0) < 0:
                    has_negative_teammate = True
                    break
            if has_negative_teammate:
                count += 1

    return count

def calculate_total_preference(TeamAssign, BestPrefMat):
    total_score = 0

    # Number of students
    NumIDs = TeamAssign.shape[0]

    # Iterate through each student
    for i in range(NumIDs):
        # Get the ID and group of the student
        student_id = TeamAssign[i, 0]
        student_group = TeamAssign[i, 1]

        # Find other members of the same group
        group_members = TeamAssign[TeamAssign[:, 1] == student_group, 0]

        # Iterate through the group members
        for member_id in group_members:
            if member_id != student_id:
                student_index = list(BestPrefMat[-1, :]).index(student_id)
                member_index = list(BestPrefMat[-1, :]).index(member_id)
                # Accumulate the preference score
                total_score += BestPrefMat[student_index, member_index]

    return total_score

for i in range(1,100):
    args=argsort(random.uniform(0,1,NumIDs))
    PrefMat=PrefMat[:,args]
    PrefMat[0:-1,:]=PrefMat[args,:]

    EgoUtil=dot(multiply(PrefMat[0:NumIDs,:],teams),ones((NumIDs,1)))
    NumNoUtil=sum(EgoUtil<=0)

    maxu=sum(EgoUtil)-30*(NumNoUtil-NumNoPrefs)
    improve=1

    while improve==1:
        improve=0
        for i in range(0,NumIDs-2) :
            for j in range(i+1,NumIDs-1) :
                newPrefMat=copy(PrefMat)
                t=copy(newPrefMat[:,i])
                newPrefMat[:,i]=newPrefMat[:,j]
                newPrefMat[:,j]=t
                t=copy(newPrefMat[i,:])
                newPrefMat[i,:]=newPrefMat[j,:]
                newPrefMat[j,:]=t
                EgoUtil=dot(multiply(newPrefMat[0:NumIDs,:],teams),ones((NumIDs,1)))
                NumNoUtil=sum(EgoUtil<=0)
                newu=sum(EgoUtil)-30*(NumNoUtil-NumNoPrefs)
                if (newu>maxu) :
                    PrefMat=newPrefMat
                    maxu=newu
                    improve=1
    EgoUtil=dot(multiply(PrefMat[0:NumIDs,:],teams),ones((NumIDs,1)))
    NumNoUtil=sum(EgoUtil<=0)
    maxu=sum(EgoUtil)-30*(NumNoUtil-NumNoPrefs)
    if (maxu>BestMax) :
        BestMax=maxu
        BestPrefMat=PrefMat
    maxu

EgoUtil=dot(multiply(BestPrefMat[0:NumIDs,:],teams),ones((NumIDs,1)))
NumNoUtil=sum(EgoUtil<=0)
maxu=sum(EgoUtil)-30*(NumNoUtil-NumNoPrefs)

tt=(transpose(list(range(NumIDs)))/4+1).astype(int)
TeamAssign=zeros((NumIDs,2))
TeamAssign[:,0]=transpose(BestPrefMat[-1,:])
TeamAssign[:,1]=transpose(tt)
#should return NumNoUtil,maxu,TeamAssign
score = calculate_total_preference(TeamAssign, BestPrefMat)
print(f"Total Preference Score: {score}")
TeamAssign
num_groups = int( int(NumIDs / 4) + int(NumIDs % 4 != 0))
older_algo_groups = [TeamAssign[TeamAssign[:, 1] == i+1, 0].tolist() for i in range(num_groups)]
tend=time.time()
print("Time Taken (to run 1 iteration): ", float(tend-tstart))
count_older_algo = count_no_positive_teammates(older_algo_groups, BestPrefMat)
count_neg_older_algo = count_no_negative_teammates(older_algo_groups, BestPrefMat)

print(f"Number of students without a preferred teammate: {count_older_algo}")


