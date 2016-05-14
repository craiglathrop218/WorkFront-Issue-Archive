#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#  WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from api import StreamClient, ObjCode, AtTaskObject


class MoveIssues(object):
    def __init__(self, api_key: str, api_path: str, move_from: str, move_to: str, age: int):
        """
        Move Issues Init
        :param api_key: The api key for auth user
        :param api_path: Path to the api
        :param move_from: ID string of project to move tasks from
        :param move_to: ID string of project to move tasks from
        :param age: Find issues with an actual completion date greater than this value in months.
        """
        self.api_key = api_key
        self.api_path = api_path
        self.move_from = move_from
        self.move_to = move_to
        self.age = age
        # Can't bluk move more than 100 elements as per API restrictions
        self.max_results = 100
        self.completion_date_str = "$$TODAY-{age}m".format(age=self.age)
        self.client = StreamClient(self.api_path, self.api_key)

    def go(self):
        """
        Starts the moving process.
        """
        results_len = 1  # Just something to get us started
        while results_len > 0:
            issues = self.find_issues()
            results_len = len(issues)
            iss_move_count = self.move_issues(issues)
            if results_len > 0:
                results_str = "Moved {result_count} items".format(result_count=iss_move_count)
                print(results_str)

        print("Operation complete")

    def find_issues(self):
        """
        Finds issues in 'from' project to be moved.
        :return: a list of issues that meet the criteria
        """
        params = {
            "$$LIMIT": self.max_results,
            "projectID": self.move_from,
            "projectID_Mod": "in",
            "actualCompletionDate": self.completion_date_str,
            "actualCompletionDate_Mod": "lte"
        }
        fields = {}
        results = AtTaskObject(self.client.search(ObjCode.ISSUE, params, fields))
        return results.data

    def move_issues(self, data) -> int:
        """
        Moves issues between projects
        :param data: list of issues
        :return: count of issues moved
        """
        counter = 0
        for item in data:
            # Get the ID number
            uid = item['ID']
            params = {'projectID': self.move_to}
            AtTaskObject(self.client.action(ObjCode.ISSUE, 'move', params, objid=uid))
            print(".", end="", flush=True)
            counter += 1
        return counter

    def get_proj_name(self, proj_id: str):
        """
        Gets the name of a project from ID
        :param proj_id: ID number of the project to get the name of
        :return: Name of the project
        """
        results = AtTaskObject(self.client.get(ObjCode.PROJECT, proj_id))
        return results.data['name']

    def get_number_of_issues_to_move(self):
        """
        Get's a count of the number of issues to be moved
        :return: a count of the number of issues to be moved
        """
        params = {
            "projectID": self.move_from,
            "projectID_Mod": "in",
            "actualCompletionDate": self.completion_date_str,
            "actualCompletionDate_Mod": "lte"
        }
        results = AtTaskObject(self.client.report(ObjCode.ISSUE, params, 'sum'))
        return results.data['dcount_ID']

user_agreement = 'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE \n' \
                 'WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR \n' \
                 'COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR \n' \
                 'OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE \n.' \
                 'AGREE? (Y / N)'

ua = str(input(user_agreement)).lower()

if ua == "y":
    sub_domain = input("Enter the sub domain: ")
    live_server = 'https://{sub_domain}.attask-ondemand.com/attask/api/v4.0/'.format(sub_domain=sub_domain)
    sandbox = 'https://{sub_domain}.attasksandbox.com/attask/api/v4.0/'.format(sub_domain=sub_domain)
    api_path = live_server if input("Select 's' for sandbox or 'l' for live: ") == "l" else sandbox
    api_key = input("Enter API Key: ")
    age = int(input("Archive issues older than ___ months (whole months only): "))
    move_from = input("Enter ID number of queue to move from: ")
    move_to = input("Enter ID number of queue to move to: ")

    if api_key != "" and api_path != "" and age > 0 and move_to != "" and move_from != "":
        mv = MoveIssues(api_key, api_path, move_from, move_to, age)

        from_name = mv.get_proj_name(move_from)
        to_name = mv.get_proj_name(move_to)

        iss_count = mv.get_number_of_issues_to_move()

        ready_msg = "*********************************************\n\n" \
                    "NOTICE: This operation will move {iss_count} issues.\n\n" \
                    "I'm ready to start moving issues older than {age} months \n" \
                    "from project {from_name} to {to_name}. \n" \
                    "Should I proceed? (y/n)".format(iss_count=iss_count,
                                                     age=age,
                                                     from_name=from_name,
                                                     to_name=to_name)

        make_it_happen = str(input(ready_msg)).lower()

        if make_it_happen == "y":
            mv.go()
        else:
            print("Exiting...")

    else:
        print('You missed an input. Please run the program again.')
