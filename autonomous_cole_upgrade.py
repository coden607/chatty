#!/usr/bin/env python3
"""
Autonomous Cole Medin Learning and System Upgrade Script
This script automatically scrapes Cole Medin's YouTube channel and upgrades CHATTY
"""

import os
import time
import requests
import json
from datetime import datetime
import argparse

class AutonomousColeUpgrade:
    def __init__(self, base_url="http://localhost:8181"):
        self.base_url = base_url
        self.session = requests.Session()

    def authenticate(self, username="admin", password="admin"):
        """Authenticate with the system"""
        try:
            response = self.session.post(f"{self.base_url}/api/auth/login", json={
                'username': username,
                'password': password
            })

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                self.session.headers.update({'Authorization': f'Bearer {token}'})
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def start_channel_scraping(self):
        """Start the Cole Medin channel scraping process"""
        try:
            print("🔍 Starting Cole Medin channel scraping...")

            response = self.session.post(f"{self.base_url}/api/cole/scrape")

            if response.status_code == 202:
                data = response.json()
                task_id = data.get('task_id')
                print(f"✅ Scraping initiated successfully (Task ID: {task_id})")
                print(f"⏱️  Estimated duration: {data.get('estimated_duration')}")
                return task_id
            else:
                print(f"❌ Failed to start scraping: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error starting scraping: {str(e)}")
            return None

    def monitor_progress(self, task_id=None):
        """Monitor the scraping progress"""
        print("📊 Monitoring scraping progress...")

        while True:
            try:
                response = self.session.get(f"{self.base_url}/api/cole/status")

                if response.status_code == 200:
                    status = response.json()

                    progress = status.get('progress', {})
                    videos_found = progress.get('videos_found', 0)
                    videos_processed = progress.get('videos_processed', 0)
                    tools_discovered = progress.get('tools_discovered', 0)
                    upgrades_applied = progress.get('upgrades_applied', 0)

                    print(f"📈 Progress: {videos_processed}/{videos_found} videos processed")
                    print(f"🔧 Tools discovered: {tools_discovered}")
                    print(f"⬆️  Upgrades applied: {upgrades_applied}")

                    if task_id and status.get('latest_task', {}).get('id') == task_id:
                        task_status = status['latest_task']['status']
                        print(f"📋 Task status: {task_status}")

                        if task_status == 'completed':
                            print("✅ Scraping completed!")
                            break
                        elif task_status == 'failed':
                            print("❌ Scraping failed!")
                            break

                    if videos_processed >= videos_found and videos_found > 0:
                        print("✅ All videos processed!")
                        break

                else:
                    print(f"❌ Failed to get status: {response.text}")

            except Exception as e:
                print(f"❌ Error monitoring progress: {str(e)}")

            time.sleep(30)  # Check every 30 seconds

    def get_extracted_knowledge(self):
        """Retrieve and display extracted knowledge"""
        try:
            print("\n📚 Retrieving extracted knowledge...")

            response = self.session.get(f"{self.base_url}/api/cole/knowledge")

            if response.status_code == 200:
                data = response.json()
                knowledge = data.get('knowledge', {})

                print("🎯 Knowledge Extraction Summary:")
                print(f"   • Total videos analyzed: {knowledge.get('total_videos_analyzed', 0)}")
                print(f"   • Technical concepts: {len(knowledge.get('technical_concepts', []))}")
                print(f"   • Tools discovered: {len(knowledge.get('tools_discovered', []))}")
                print(f"   • Programming languages: {len(knowledge.get('programming_languages', []))}")
                print(f"   • AI techniques: {len(knowledge.get('ai_techniques', []))}")

                print("\n🔧 Top Tools Discovered:")
                for tool in knowledge.get('tools_discovered', [])[:10]:
                    print(f"   • {tool}")

                print("\n🤖 AI Techniques Learned:")
                for technique in knowledge.get('ai_techniques', [])[:10]:
                    print(f"   • {technique}")

                return knowledge
            else:
                print(f"❌ Failed to get knowledge: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error getting knowledge: {str(e)}")
            return None

    def trigger_system_upgrade(self):
        """Trigger autonomous system upgrade"""
        try:
            print("\n⬆️  Triggering autonomous system upgrade...")

            response = self.session.post(f"{self.base_url}/api/cole/upgrade")

            if response.status_code == 200:
                data = response.json()
                results = data.get('upgrade_results', {})

                print("✅ System upgrade completed!")
                print(f"🔧 Tools installed: {len(results.get('tools_installed', []))}")
                print(f"🤖 Agents created: {len(results.get('agents_created', []))}")
                print(f"⚠️  Errors: {len(results.get('errors', []))}")

                if results.get('tools_installed'):
                    print("\n📦 Installed Tools:")
                    for tool in results['tools_installed']:
                        print(f"   ✅ {tool}")

                if results.get('agents_created'):
                    print("\n🤖 Created Agents:")
                    for agent in results['agents_created']:
                        print(f"   ✅ {agent}")

                if results.get('errors'):
                    print("\n❌ Errors:")
                    for error in results['errors']:
                        print(f"   ❌ {error}")

                return results
            else:
                print(f"❌ Upgrade failed: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error triggering upgrade: {str(e)}")
            return None

    def create_specialized_agents(self, knowledge):
        """Create specialized agents based on extracted knowledge"""
        try:
            print("\n🏗️  Creating specialized agents...")

            themes = knowledge.get('key_themes', [])
            created_agents = []

            for theme_data in themes[:3]:  # Top 3 themes
                theme = theme_data['theme']

                print(f"🤖 Creating agent for theme: {theme}")

                response = self.session.post(f"{self.base_url}/api/cole/create-specialized-agent", json={
                    'theme': theme
                })

                if response.status_code == 201:
                    data = response.json()
                    agent = data.get('agent', {})
                    print(f"   ✅ Created agent: {agent.get('name')}")
                    created_agents.append(agent)
                else:
                    print(f"   ❌ Failed to create agent for {theme}: {response.text}")

            return created_agents

        except Exception as e:
            print(f"❌ Error creating specialized agents: {str(e)}")
            return []

    def run_complete_upgrade_cycle(self):
        """Run the complete Cole Medin learning and upgrade cycle"""
        print("🚀 Starting Complete Cole Medin Learning & Upgrade Cycle")
        print("=" * 60)

        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed.")
            return False

        # Step 2: Start channel scraping
        task_id = self.start_channel_scraping()
        if not task_id:
            print("❌ Failed to start channel scraping.")
            return False

        # Step 3: Monitor progress
        self.monitor_progress(task_id)

        # Step 4: Get extracted knowledge
        knowledge = self.get_extracted_knowledge()
        if not knowledge:
            print("❌ No knowledge extracted.")
            return False

        # Step 5: Trigger system upgrade
        upgrade_results = self.trigger_system_upgrade()
        if not upgrade_results:
            print("❌ System upgrade failed.")
            return False

        # Step 6: Create specialized agents
        if knowledge.get('key_themes'):
            specialized_agents = self.create_specialized_agents(knowledge)
            print(f"\n🤖 Total specialized agents created: {len(specialized_agents)}")

        print("\n🎉 Cole Medin Learning & Upgrade Cycle Completed Successfully!")
        print("=" * 60)
        print("📊 Summary:")
        print(f"   • Videos analyzed: {knowledge.get('total_videos_analyzed', 0)}")
        print(f"   • Tools discovered: {len(knowledge.get('tools_discovered', []))}")
        print(f"   • Agents created: {len(upgrade_results.get('agents_created', [])) + len(specialized_agents) if 'specialized_agents' in locals() else 0}")
        print(f"   • System improvements: {len(upgrade_results.get('improvements_made', []))}")

        return True

def main():
    parser = argparse.ArgumentParser(description='Autonomous Cole Medin Learning & Upgrade')
    parser.add_argument('--username', default='admin', help='Admin username')
    parser.add_argument('--password', default='admin', help='Admin password')
    parser.add_argument('--url', default='http://localhost:8181', help='CHATTY API URL')

    args = parser.parse_args()

    upgrader = AutonomousColeUpgrade(args.url)

    success = upgrader.run_complete_upgrade_cycle()

    if success:
        print("\n🎯 CHATTY has successfully learned from Cole Medin's teachings!")
        print("🔮 The system is now armed with advanced AI tools and capabilities.")
        exit(0)
    else:
        print("\n❌ Learning and upgrade cycle failed.")
        exit(1)

if __name__ == '__main__':
    main()
